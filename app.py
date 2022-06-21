# packages for working with our data
import pandas as pd
import numpy as np

# page we'll use to access the data
#import ulmo
import nasa

# packages for plotting
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.collections import PatchCollection
from matplotlib.colors import ListedColormap

import streamlit as st


st.set_page_config(page_title="#ShowYourStripes", page_icon="🥵")

################################################################################
# Get city name / coords data
################################################################################

@st.cache
def get_city_data():
    df_cities = pd.read_csv("https://raw.githubusercontent.com/kelvins/US-Cities-Database/main/csv/us_cities.csv")
    df_cities['name_with_state'] = df_cities['CITY'] + ', ' + df_cities['STATE_CODE']
    df_cities = df_cities.set_index('name_with_state')[['LATITUDE', 'LONGITUDE']].sort_index()
    return df_cities

df_cities = get_city_data()

city = st.selectbox("city", options=df_cities.index, index=df_cities.index.to_list().index("Seattle, WA"))

coords = df_cities.loc[city]
latitude = coords['LATITUDE']
longitude = coords['LONGITUDE']

################################################################################
# Get met data
################################################################################

@st.cache
def get_met_data(latitude, longitude):
    df = nasa.get_daymet_singlepixel(latitude, longitude, variables=['tmax', 'tmin'], years=None, as_dataframe=True)

    df['tmean'] = np.mean([df.tmax, df.tmin], axis=0)
    df_annual = df.resample('Y').mean()
    climate_mean = df_annual.tmean.mean()
    df_annual['anomaly'] = df_annual.tmean - climate_mean
    df_annual['year'] = df_annual['year'].astype(int)
    return df, df_annual

df, df_annual = get_met_data(latitude, longitude)


################################################################################
# Create figure
################################################################################

cmap = ListedColormap([
    '#08306b', '#08519c', '#2171b5', '#4292c6',
    '#6baed6', '#9ecae1', '#c6dbef', '#deebf7',
    '#fee0d2', '#fcbba1', '#fc9272', '#fb6a4a',
    '#ef3b2c', '#cb181d', '#a50f15', '#67000d',
])

rect_ll_y = df_annual.anomaly.min() # rectangle lower left y coordinate, minimum anomaly value
rect_height = np.abs(df_annual.anomaly.max()-df_annual.anomaly.min()) # rectangle height, range between min and max anomaly values
year_start = df_annual.year.min() # year to start the plot x axis
year_end = df_annual.year.max() + 1 # year to end the plot x axis

# create a collection with a rectangle for each year
col = PatchCollection([
Rectangle((x, rect_ll_y), 1, rect_height)
for x in range(year_start, year_end)
])

# Create the figure, assign the data, colormap and color limits and add it to the figure axes
fig = plt.figure(figsize=(5, 1))

# set up the axes
ax = fig.add_axes([0, 0, 1, 1])
ax.set_axis_off()

# set data, colormap and color limits
col.set_array(df_annual.anomaly) # use the anomaly data for the colormap
col.set_cmap(cmap) # apply our custom red/blue colormap colors
col.set_clim(-rect_height/2, rect_height/2) # set the limits of our colormap
ax.add_collection(col)

# plot anomaly graph
df_annual.plot(x='year', y='anomaly', linestyle='-',lw=3,color='w',ax=ax, legend=False)
# plot horizontal line at zero anomaly
ax.axhline(0, linestyle='--', color='w')
# plot a text label
ax.text(df.year.max()+3,-.4,city, fontsize=30, fontweight='bold', color='k')

# Make sure the axes limits are correct and save the figure.
ax.set_ylim(-rect_height/2, rect_height/2) # set y axis limits to rectanlge height centered at zero
ax.set_xlim(year_start, year_end); # set x axes limits to start and end year

st.write(fig)

st.markdown("Based on [this repo](https://github.com/spestana/ulmo-warming-stripes) by [Steven Pestana](https://twitter.com/stevenpest), city data from [here](https://github.com/kelvins/US-Cities-Database) by [Kelvin S. do Prado](https://twitter.com/kelvinsprado)")
