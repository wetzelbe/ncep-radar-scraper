import sys
import time
import os
import requests
from bs4 import BeautifulSoup
import urllib.request
import datetime

TARGET_PATH = sys.argv[1]
BASE_DOMAIN = "https://mrms.ncep.noaa.gov/2D"
SUB_DATASETS = [
    ("", "CONTINENTAL"),
    ("/HAWAII", "HAWAII"),
    ("/CARIB", "CARIB"),
    ("/ALASKA", "ALASKA")
]

DIRECTORY = "/MergedBaseReflectivityQC"

while True:
    try:
        print(datetime.datetime.now())
        for sub_dataset, sub_dataset_path in  SUB_DATASETS:
            print(sub_dataset_path)
            response = requests.get(BASE_DOMAIN + sub_dataset + DIRECTORY)
            soup = BeautifulSoup(response.content, 'html.parser')
            rows = soup.table.find_all('tr')

            stats = dict(
                total = len(rows),
                skipped = 0,
                ignored = 0,
                exists = 0,
                downloaded = 0,
                error = 0
            )

            for row in rows:
                try:
                    filename = row.find_all('td')[0].find('a').attrs["href"]
                    if ".grib2.gz" in filename and not "latest" in filename:
                        timestamp = filename.split("_")[3]
                        day = timestamp.split("-")[0]

                        # Check if we have file
                        target = os.path.join(TARGET_PATH, sub_dataset_path, day)
                        if not os.path.isdir(target):
                            print(" Creating day directory", end=" ")
                            os.makedirs(target)
                        existing_files = os.listdir(target)
                        if not filename in existing_files:
                            print(" Downloading", end=" ")
                            path, msg = urllib.request.urlretrieve(BASE_DOMAIN + sub_dataset + DIRECTORY + "/" + filename, os.path.join(TARGET_PATH, 'temp.gz'))
                            print(" -> ", path, end=" ")
                            os.rename(path, os.path.join(target, filename))
                            print(" -> ", os.path.join(target, filename))
                            stats["downloaded"] += 1
                        else:
                            stats["exists"] += 1
                    else:
                        stats["ignored"] += 1
                except IndexError:
                    stats["skipped"] += 1
                except KeyboardInterrupt as e:
                    raise e 
                except Exception as e:
                    stats["error"] += 1
            print("", stats)
    except KeyboardInterrupt as e:
        print("exiting")
        sys.exit()
    except Exception as e:
        print("Some exception occurred, trying again in 120 seconds")
        print(e)
    print()
    time.sleep(120)
