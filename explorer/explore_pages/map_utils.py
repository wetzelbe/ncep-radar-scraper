import plotly.graph_objects as go
from PIL import Image
import numpy as np
import urllib
import streamlit as st
import rioxarray as rxr
import math
import requests
import io

@st.cache_data
def tile_array(url:str) -> np.ndarray:
    try:
        headers = {"User-Agent": "TileFetcher/1.0 (your_email@example.com)"}
        with requests.get(url,headers=headers) as req:
            pil_image = Image.open(io.BytesIO(req.content)).convert("RGB")
            im = np.array(pil_image)
    except Exception as e:
        print(e)
        print("Could not get " + url)
        im = np.zeros((256,256,3))
    return im

def add_satellite_imagery(fig: go.Figure, level: int, radar_bounds: tuple[tuple[float, float], tuple[float, float]], base_url: str):
    n = 2 ** level
    xs = []
    x_tile_min = math.floor(n * radar_bounds[0][0] / 256)
    x_tile_max = math.floor(n * radar_bounds[0][1] / 256)
    
    y_tile_min = math.floor(n * radar_bounds[1][0] / 256)
    y_tile_max = math.floor(n * radar_bounds[1][1] / 256)

    progress = st.progress(0, "Downloading tiles")
    for x in range(x_tile_min, x_tile_max + 1):
        ys = []
        for y in range(y_tile_min, y_tile_max + 1):
            url = base_url.format(z=level, x=x, y=y)
            im = tile_array(url)
            ys.append(im)
            progress.progress(int((x + ((y-y_tile_min)/(y_tile_max + 1 - y_tile_min)) - x_tile_min)/(x_tile_max + 1 - x_tile_min) * 100), "Downloading tiles, x=" + str(x) + ", y=" + str(y))
        xs.append(np.concatenate(ys, axis=0))
        
    progress.empty()

    merged = np.concatenate(xs, axis=1)
    fig.add_trace(
        go.Image(z=merged, 
                    dx=1 / 2 ** level, 
                    dy=1 / 2**level,
                    x0=1 / 2 ** level / 2 + x_tile_min * 256 / n,
                    y0=1 / 2 ** level / 2 + y_tile_min * 256 / n,
                    name="Satellite")
    )
        

@st.cache_data
def read_elevation_data():
  elevation = rxr.open_rasterio('elevation_continental_us.tif', masked=True)
  elevation_np = np.array(elevation.as_numpy()).reshape(elevation.shape[1:3])
  elevation_bounds = elevation.rio.bounds()
  elevation_by_position = np.array([[[360 + x / elevation_np.shape[1] * (elevation_bounds[2] - elevation_bounds[0]) + elevation_bounds[0], 
                                      (1 - y / elevation_np.shape[0]) * (elevation_bounds[3] - elevation_bounds[1]) + elevation_bounds[1],
                                      value] for x, value in enumerate(row)] for y, row in enumerate(elevation_np)]).reshape((-1,3))
  elevation_by_position = elevation_by_position[~np.isnan(elevation_by_position[:,2])]

  elevation_by_position[:,0] = (elevation_by_position[:,0] + 180) % 360 - 180
  elevation_by_position[:,1] = (elevation_by_position[:,1] + 90) % 180 - 90
  return elevation_by_position

@st.cache_data
def get_elevation_image(resolution = 1, radar_bounds=((-180,180), (-90,90))):
  elevation_by_position = read_elevation_data()

  elevation_by_position = elevation_by_position[elevation_by_position[:,0] > radar_bounds[0][0]]
  elevation_by_position = elevation_by_position[elevation_by_position[:,0] < radar_bounds[0][1]]
  elevation_by_position = elevation_by_position[elevation_by_position[:,1] > radar_bounds[1][0]]
  elevation_by_position = elevation_by_position[elevation_by_position[:,1] < radar_bounds[1][1]]

  hist = np.histogram2d(elevation_by_position[:,1], elevation_by_position[:,0], bins=[360*resolution, 180*resolution], density=True, weights=elevation_by_position[:,2], )
  hist = list(hist)
  hist[1] = np.array(hist[1])
  hist[2] = np.array(hist[2])
  return tuple(hist)