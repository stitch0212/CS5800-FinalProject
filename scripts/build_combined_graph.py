import requests
import json
from datetime import datetime
import numpy as np
from pathlib import Path
import time
import osmnx as ox
import networkx as nx
from scipy.interpolate import griddata

def parse_speed_limit(speed_str):
    """
    Parse speed limit string that might contain multiple values.
    
    Args:
        speed_str: Speed limit string from OSM data
        
    Returns:
        float: Speed limit in km/h
    """
    if not speed_str:
        return None
        
    try:
        # If it's already a number, return it
        return float(speed_str)
    except (ValueError, TypeError):
        try:
            # If it's a string with multiple values (e.g., "30;50"), take the average
            speeds = [float(s.strip()) for s in str(speed_str).split(';')]
            return sum(speeds) / len(speeds)
        except (ValueError, TypeError):
            # If we can't parse it, return None
            return None

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

def calculate_road_solar_exposure(G, api_key, grid_size=0.05):
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
    
    return G

def calculate_travel_times(G):
    """
    Calculate travel times for each road segment including traffic signals and other delays.
    """
    # Default speed limits (km/h) based on road type
    default_speeds = {
        'motorway': 100,    # Highways
        'trunk': 80,        # Major arterial roads
        'primary': 60,      # Primary roads
        'secondary': 50,    # Secondary roads
        'tertiary': 40,     # Tertiary roads
        'residential': 30,  # Residential streets
        'service': 20,      # Service roads
        'unclassified': 30, # Unclassified roads
        'default': 30       # Default if road type unknown
    }
    
    # Traffic signal delays (minutes)
    signal_delays = {
        'traffic_signals': 1.0,     # Average wait at traffic lights
        'stop_sign': 0.5,          # Stop sign delay
        'crossing': 0.3,           # Pedestrian crossing
        'yield': 0.2,             # Yield sign
        'default': 0.2            # Default intersection delay
    }
    
    # Peak hour factors (multipliers for different road types)
    peak_hour_factors = {
        'motorway': 1.3,
        'trunk': 1.4,
        'primary': 1.5,
        'secondary': 1.4,
        'tertiary': 1.3,
        'residential': 1.2,
        'default': 1.3
    }
    
    print("Calculating travel times for each road segment...")
    total_signals = 0
    total_intersections = 0
    
    for u, v, data in G.edges(data=True):
        # 1. Get basic road info
        road_type = data.get('highway', 'default')
        if isinstance(road_type, list):
            road_type = road_type[0]
            
        length = float(data.get('length', 0))  # Length in meters
        
        # 2. Determine speed
        speed_str = data.get('maxspeed')
        speed = parse_speed_limit(speed_str)
        if speed is None:
            speed = default_speeds.get(road_type, default_speeds['default'])
        
        # 3. Calculate base travel time (minutes)
        base_time = (length / 1000) / (speed / 60)
        
        # 4. Add intersection and signal delays
        delay_time = 0
        
        # Check for traffic signals
        if data.get('traffic_signals') or data.get('highway') == 'traffic_signals':
            delay_time += signal_delays['traffic_signals']
            total_signals += 1
        
        # Check for intersections
        if data.get('junction') or len(G[u]) > 2 or len(G[v]) > 2:
            delay_time += signal_delays['default']
            total_intersections += 1
        
        # 5. Apply peak hour factor
        peak_factor = peak_hour_factors.get(road_type, peak_hour_factors['default'])
        
        # 6. Calculate final travel time
        travel_time = (base_time + delay_time) * peak_factor
        
        # Store all calculated values
        data['travel_time'] = float(travel_time)
        data['base_time'] = float(base_time)
        data['delay_time'] = float(delay_time)
        data['peak_factor'] = float(peak_factor)
        data['speed_limit'] = float(speed)
        data['weight'] = float(travel_time)
    
    # Print detailed statistics
    print("\nNetwork Statistics:")
    print(f"Total traffic signals detected: {total_signals}")
    print(f"Total intersections detected: {total_intersections}")
    
    times = [data['travel_time'] for _, _, data in G.edges(data=True)]
    base_times = [data['base_time'] for _, _, data in G.edges(data=True)]
    
    print("\nTravel Time Analysis:")
    print(f"Average base time per segment: {np.mean(base_times):.2f} minutes")
    print(f"Average actual time per segment: {np.mean(times):.2f} minutes")
    print(f"Average delay factor: {np.mean(times) / np.mean(base_times):.2f}x")
    
    # Example route statistics
    print("\nExample Route Statistics (1km distance):")
    example_time = 1 / (default_speeds['primary'] / 60)  # 1km on primary road
    print(f"Base time (no delays): {example_time:.1f} minutes")
    print(f"With traffic signal: {(example_time + signal_delays['traffic_signals']):.1f} minutes")
    print(f"With peak hour traffic: {(example_time + signal_delays['traffic_signals']) * peak_hour_factors['primary']:.1f} minutes")
    
    return G

def create_combined_graph(location, output_path, nrel_api_key):
    """
    Extract the road network, calculate travel times, and add solar exposure data.
    
    Args:
        location (str): The location name (e.g., "Vancouver, British Columbia, Canada").
        output_path (str): The file path to save the combined GraphML file.
        nrel_api_key (str): The NREL API key.
    """
    # Extract the road network
    print(f"Extracting road network for {location}...")
    G = ox.graph_from_place(location, network_type="drive")
    
    # Add basic attributes
    for _, _, data in G.edges(data=True):
        data['solar_exposure'] = 0.0
        data['travel_time'] = 0.0
    
    # Calculate travel times
    G = calculate_travel_times(G)
    
    # Calculate solar exposure
    G = calculate_road_solar_exposure(G, nrel_api_key)

    for u, v, data in G.edges(data=True):
        data['weight'] = float(data['weight'])
        
    print("\nChecking Edge Attributes:")
    for u, v, data in G.edges(data=True):
        print(f"Edge ({u}, {v}): travel_time={data['travel_time']}, type={type(data['travel_time'])}")
    
    # Save the combined graph
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    ox.save_graphml(G, output_path)
    print(f"Combined graph saved at {output_path}")
    
    return G

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    # Get NREL API key from environment variable
    nrel_api_key = "ATZpaclpEhaBRjGpfZiOBKnkD2eiLTHUBLs0FIIH"
    if not nrel_api_key:
        print("Error: NREL_API_KEY not found in environment variables")
        exit(1)
        
    location = "Los Angeles, California, USA"
    output_path = "../data/road_network_combined.graphml"

    G = create_combined_graph(location, output_path, nrel_api_key)