import sys
import xarray as xr
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import gzip
import streamlit as st
import os
from explore_pages.map_utils import add_satellite_imagery, get_elevation_image

DATASET_BASE_DIR = sys.argv[1]

bamako= [[0.0, 'rgb(0, 63, 76)'], # a scientific colorscale for dem data
[0.1, 'rgb(29, 81, 59)'],
[0.2, 'rgb(55, 98, 43)'],
[0.3, 'rgb(79, 114, 30)'],
[0.4, 'rgb(103, 129, 16)'],
[0.5, 'rgb(136, 142, 2)'],
[0.6, 'rgb(169, 154, 21)'],
[0.7, 'rgb(192, 171, 45)'],
[0.8, 'rgb(214, 188, 74)'],
[0.9, 'rgb(234, 209, 112)'],
[1.0, 'rgb(254, 229, 152)']]

dem = [
  [0.0, 'green'],
  [0.8, 'brown'],
  [1.0, 'white']
]

radar_color_scale = px.colors.sequential.Electric
radar_color_scale[0] = 'rgba(0,0,0,0)'

st.subheader(":material/layers: Layers")

layer_columns = st.columns(3)
with layer_columns[0].popover(":material/map:", width='stretch'):
  SHOW_MAP = not st.checkbox("Hide", value=False)
  BASE_MAP = st.selectbox("Map provider", [
    "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}",
    "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
  ], disabled=not SHOW_MAP)
  MAP_LEVEL = st.number_input("Map level", min_value=0, max_value=23, value=2, disabled=not SHOW_MAP)
  CROP_TO_RADAR = st.checkbox("Crop to radar", disabled=not SHOW_MAP, value=True)

with layer_columns[1].popover(":material/radar:", width='stretch'):
  col1, col2 = st.columns(2)

  SUB_DATASET = col1.selectbox("Sub dataset", ["CONTINENTAL", "CARIB", "HAWAII", "ALASKA"])

  day_options = os.listdir(os.path.join(DATASET_BASE_DIR, SUB_DATASET))
  day_options.sort(reverse=True)
  DAY = col2.selectbox("Day", day_options)

  file_options = os.listdir(os.path.join(DATASET_BASE_DIR, SUB_DATASET, DAY))
  file_options.sort(reverse=True)
  FILE = st.selectbox("File", file_options)

  filename = os.path.join(DATASET_BASE_DIR, SUB_DATASET, DAY, FILE)
  RADAR_RESOLUTION = st.number_input("Radar resolution", min_value=1, value=10, max_value=500)

with layer_columns[2]:
  st.button(label=":material/autorenew:", width='stretch')

with st.spinner("Plotting"):
  if filename.endswith(".gz"):
    with open(filename, 'rb') as f:
      uncompressed = gzip.decompress(f.read())
      with open("temp.grib2", 'wb') as g:
        g.write(uncompressed)
        filename = "temp.grib2"

  ds = xr.open_dataset(filename, engine="cfgrib")
  ds = ds.get("unknown")

  df = ds.to_dataframe()
  df = df.reset_index()

  df = df[df['unknown'] > 0]
  df['longitude'] = (df['longitude'] + 180) % 360 - 180
  df['latitude'] = (df['latitude'] + 90) % 180 - 90

  radius = 256 / (2 * np.pi)
  df['latitude_radians'] = df['latitude'] * np.pi / 180
  df['longitude_radians'] = df['longitude'] * np.pi / 180 + np.pi

  df['x'] = (0.5 + df['longitude'] / 360) * 256
  df['y'] = (0.5 - np.arcsinh(np.tan(df['latitude_radians'])) / (2*np.pi)) * 256
  
  radar_bounds = ((df['longitude'].min(), df['longitude'].max()), (df['latitude'].min(), df['latitude'].max()))
  radar_bounds_image = ((df['x'].min(), df['x'].max()), (df['y'].min(), df['y'].max()))
  radar_nbinsx = int(np.ceil(radar_bounds[0][1] - radar_bounds[0][0]))
  radar_nbinsy = int(np.ceil(radar_bounds[1][1] - radar_bounds[1][0]))

  fig = go.Figure()
  if SHOW_MAP:
    if CROP_TO_RADAR:
      add_satellite_imagery(fig, MAP_LEVEL, radar_bounds_image, BASE_MAP)
    else:
      add_satellite_imagery(fig, MAP_LEVEL, ((0,255), (0,255)), BASE_MAP)
  #fig.add_trace(go.Heatmap(z=elevation_map[0], name="Elevation", colorscale='Greys' , x=elevation_map[2], y=elevation_map[1]))
  fig.add_trace(go.Histogram2d(x=df['x'], y=df['y'], z=df['unknown'], name="Radar", histfunc='avg', nbinsx=radar_nbinsx*RADAR_RESOLUTION, nbinsy=radar_nbinsy*RADAR_RESOLUTION, colorscale=radar_color_scale))
  fig.update_yaxes(
      scaleanchor="x",
      scaleratio=1,
      autorange="reversed"
  )
  fig.update_xaxes(showticklabels=False)
  fig.update_yaxes(showticklabels=False)
  fig.update_layout(
    autosize=True,
    height=600
  )
  
with st.spinner("Loading plot"):
  st.plotly_chart(fig)