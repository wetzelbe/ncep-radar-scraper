import sys
import streamlit as st
import os
import calmap
import pandas as pd
import matplotlib.pyplot as plt
import subprocess
import numpy as np

DATASET_BASE_DIR = sys.argv[1]
SUB_DATASETS = ["CONTINENTAL", "CARIB", "HAWAII", "ALASKA"]
labels = [":material/activity_zone: " + sub_dataset.capitalize() if sub_dataset != 'CARIB' else ":material/activity_zone: Caribbean" for sub_dataset in SUB_DATASETS]
st.title("Dataset overview")

st.button(label=":material/autorenew:")

tabs = st.tabs(labels)


for sub_dataset, tab in zip(SUB_DATASETS, tabs):
    # Size on disk
    size_on_disk_process = subprocess.run(["du", "-sh", os.path.join(DATASET_BASE_DIR, sub_dataset)], stdout=subprocess.PIPE)
    size_on_disk = size_on_disk_process.stdout.decode().split("\t")[0]

    # Timepoints per day
    days = os.listdir(os.path.join(DATASET_BASE_DIR, sub_dataset))
    counts = []
    for day in days:
        counts.append(len(os.listdir(os.path.join(DATASET_BASE_DIR, sub_dataset, day))))
    overall_count = np.array(counts).sum()
    tab.markdown(":blue-badge[:material/123: " + str(overall_count) + "] :blue-badge[:material/database: " + size_on_disk +"]")

    df = pd.DataFrame({
        "day": days,
        "n": counts
    })
    df['day'] = pd.to_datetime(df['day'], format='%Y%m%d')
    df = df.set_index('day').sort_index()
    fig, ax = plt.subplots()
    calmap.yearplot(df, ax=ax, dayticks=[], monthticks=[], cmap="YlGn", linecolor=(14/255, 17/255, 23/255), fillcolor=(26/255, 28/255, 36/255))
    ax.axes.axis(False)
    tab.pyplot(fig, transparent=True)
    with tab.expander("Data"):
        st.dataframe(df)

    
    

        
