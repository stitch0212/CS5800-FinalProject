import requests
import json
from datetime import datetime
import numpy as np
from pathlib import Path
import time
import osmnx as ox
from scipy.interpolate import griddata

def create_grid(G, grid_size=0.01):
    """Create a grid covering the network area"""
    lats, lons = [], []
    for _, _, data in G.edges(data=True):
        if 'geometry' in data:
            coords = list(data['geometry'].coords)
            lats.extend([coord[1] for coord in coords])
            lons.extend([coord[0] for coord in coords])
    
    min_lat, max_lat = min(lats) - grid_size, max(lats) + grid_size
    min_lon, max_lon = min(lons) - grid_size, max(lons) + grid_size
    
    lat_points = np.arange(min_lat, max_lat, grid_size)
    lon_points = np.arange(min_lon, max_lon, grid_size)
    
    grid_points = [(lat, lon) for lat in lat_points for lon in lon_points]
    return grid_points

def calculate_road_solar_exposure(G, api_key, output_path=None, grid_size=0.05):  # Increased grid size
    base_url = "https://developer.nrel.gov/api/solar/solar_resource/v1.json"
    cache_dir = Path("data/cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    grid_points = create_grid(G, grid_size)
    print(f"Created grid with {len(grid_points)} points")
    
    solar_values = []
    for i, (lat, lon) in enumerate(grid_points):
        if i % 10 == 0:  # Progress update
            print(f"Processing point {i+1}/{len(grid_points)}")
            
        cache_file = cache_dir / f"solar_{lat:.4f}_{lon:.4f}.json"
        
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                solar_data = json.load(f)
                print(f"Using cached data for point {i+1}")
        else:
            try:
                params = {'api_key': api_key, 'lat': lat, 'lon': lon}
                response = requests.get(base_url, params=params)
                response.raise_for_status()
                solar_data = response.json()
                
                with open(cache_file, 'w') as f:
                    json.dump(solar_data, f)
                
                print(f"Fetched new data for point {i+1}")
                time.sleep(0.6)  # Increased delay between requests
            except Exception as e:
                print(f"Error at point {i+1}: {str(e)}")
                solar_data = None
        
        if solar_data:
            outputs = solar_data.get('outputs', {})
            avg_dni = outputs.get('avg_dni', {}).get('annual', 0)
            avg_ghi = outputs.get('avg_ghi', {}).get('annual', 0)
            solar_values.append((avg_dni + avg_ghi) / 2)
        else:
            solar_values.append(0)
    
    print("Interpolating values for road segments...")
    for u, v, data in G.edges(data=True):
        if 'geometry' in data:
            coords = list(data['geometry'].coords)
            points = np.array([(coord[1], coord[0]) for coord in coords])
            solar_exposure = griddata(
                np.array(grid_points),
                np.array(solar_values),
                points,
                method='linear',
                fill_value=0
            ).mean()
            
            data['solar_exposure'] = float(solar_exposure)
            data['weight'] = float(solar_exposure)
    
    if output_path:
        ox.save_graphml(G, output_path)
    
    return G

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    import osmnx as ox

    # Load environment variables
    load_dotenv()

    # Get NREL API key from environment variable
    nrel_api_key = os.getenv('NREL_API_KEY')
    if not nrel_api_key:
        print("Error: NREL_API_KEY not found in environment variables")
        exit(1)
        
    graph_path = "../data/road_network.graphml"
    G = ox.load_graphml(graph_path)

    G_solar = calculate_road_solar_exposure(
        G,
        nrel_api_key,
        output_path="../data/road_network_solar_weighted.graphml"
    )
