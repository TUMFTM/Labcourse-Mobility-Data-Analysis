import folium
import os
from folium.plugins import MarkerCluster
from folium import plugins
import geojson as gj
from pylab import cm
import matplotlib
import numpy as np


# Create a array of colors as colorbar
def create_cm(mini, maxi, step, cm_type):
    output=[]
    # https://matplotlib.org/examples/color/colormaps_reference.html
    #print((mini, maxi))
    #print(int((maxi-mini)/step))
    maxi += abs(mini) if mini < 0 else 0 # shift colorbar if negative values
    mini = 0 if mini < 0 else mini
    cmap = cm.get_cmap(cm_type, int((maxi-mini)/step))    # PiYG
    for i in range(int(mini/step)): output.append('0')
    for i in range(cmap.N):
        rgb = cmap(i)[:3] # will return rgba, we take only first 3 so we get rgb
        output.append(matplotlib.colors.rgb2hex(rgb))
    return output

def map_folium(pos_data, colorvalue, geometry = 'geom', c_min = -1, c_max = -1, line = False, cm_type='jet'):
    # create map
    print ("Rendering " + str(pos_data.shape[0]) + " Points")
    if pos_data.shape[0] > 6500:
        print("Too many points, render would fail")
        return
    center_coordinates = [48.265035, 11.668141] # Garching
    points_map = folium.Map(location=center_coordinates, zoom_start=12, tiles='cartodbpositron', width=1800, height=1200, prefer_canvas=False)
    folium.TileLayer('Stamen Terrain').add_to(points_map)
    folium.TileLayer('CartoDB dark_matter').add_to(points_map)
    
    cm_scale = 0.1
    cm_min = min(pos_data[colorvalue]) if (c_min ==-1 and c_max ==-1) else c_min
    cm_max = max(pos_data[colorvalue]) if (c_min ==-1 and c_max ==-1) else c_max

    cm=create_cm(cm_min, cm_max, cm_scale, cm_type)
    
    # create geojson points from dafaframe
    features = []
    count = 0
    for idx, row in pos_data.iterrows():
        count += 1
        if (pos_data.shape[0]- count) > 1:
            geom = row[geometry]
            geom_next = pos_data.iloc[count+1][geometry]
            row[colorvalue] += cm_min if cm_min < 0 else 0 # if negative value, shift colorbar
            #print(row[colorvalue]/cm_scale)
            cm_pos = int(np.clip(row[colorvalue]/cm_scale,cm_min/cm_scale, cm_max/cm_scale))-1
            #print (cm_pos)
            if line: features.append(gj.Feature(geometry=gj.LineString([(geom.x, geom.y), (geom_next.x, geom_next.y)]), properties={"stroke": cm[cm_pos], "stroke-opacity": 1,"stroke-width": 5}))
            else: features.append(gj.Feature(geometry=gj.LineString([(geom.x, geom.y), (geom.x, geom.y)]), properties={"stroke": cm[cm_pos], "stroke-opacity": 1,"stroke-width": 5}))
    # safe geojson to file
    with open("exports.geojson", 'w') as outfile:
        out_data=gj.FeatureCollection(features)
        gj.dump(out_data, outfile)

    # import geojson
    folium.GeoJson(data=open("exports.geojson", "r", encoding="utf-8-sig").read(),style_function=lambda x: {
            'color' : x['properties']['stroke'],
            'weight' : x['properties']['stroke-width'],
            'opacity': 0.6#,
            #'fillColor' : x['properties']['fill'],
            }, name = colorvalue).add_to(points_map)
    
    folium.LayerControl().add_to(points_map)
    # ToDo: fix colorbar
    #cm.caption = 'Speed'
    #points_map.add_child(cm)

    # Fullscreen mode
    plugins.Fullscreen(position='topright', force_separate_button=True).add_to(points_map)

    # claculate bounds of track
    geom = pos_data[geometry]
    bounds = [[min(geom.y),min(geom.x)],[max(geom.y),max(geom.x)]]
    points_map.fit_bounds(bounds)
    return points_map

def lat_lon_2_m(latitude_1, longitude_1, latitude_2, longitude_2):
    # Radius of the earth in km
    radius_earth = 6371009
    d_latitude = np.deg2rad(latitude_2 - latitude_1)
    d_longitude = np.deg2rad(longitude_2 - longitude_1)
    latitude_1 = np.deg2rad(latitude_1)
    latitude_2 = np.deg2rad(latitude_2)

    a = (np.sin(d_latitude / 2)) ** 2 + np.cos(latitude_1) * np.cos(latitude_2) * (np.sin(d_longitude / 2)) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    distance = radius_earth * c

    return distance