import osmnx as ox
import json
from pathlib import Path
import numpy as np
from datetime import datetime

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

def calculate_travel_times(graph_path, output_path):
    """
    Calculate travel times for each road segment including traffic signals and other delays.
    """
    print("Loading road network...")
    G = ox.load_graphml(graph_path)
    
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
        data['travel_time'] = travel_time
        data['base_time'] = base_time
        data['delay_time'] = delay_time
        data['peak_factor'] = peak_factor
        data['speed_limit'] = speed
        data['weight'] = travel_time  # For routing algorithms
        
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
    
    # Save updated graph
    print("\nSaving updated graph...")
    updated_graph_path = str(Path(graph_path).parent / "road_network_time_weighted.graphml")
    ox.save_graphml(G, updated_graph_path)
    
    return G

def detect_traffic_signals(G):
    """
    Detect and count traffic signals in the network.
    Returns dictionary with signal locations and counts.
    """
    signals = {
        'nodes': [],
        'edges': [],
        'count': 0
    }
    
    # Check nodes for traffic signals
    for node, data in G.nodes(data=True):
        if ('traffic_signals' in data or 
            'highway' in data and data['highway'] == 'traffic_signals'):
            signals['nodes'].append(node)
            signals['count'] += 1
    
    # Check edges for traffic signals
    for u, v, data in G.edges(data=True):
        if ('traffic_signals' in data or 
            'highway' in data and data['highway'] == 'traffic_signals'):
            signals['edges'].append((u, v))
            signals['count'] += 1
    
    return signals

def create_time_weighted_graph(base_graph_path, travel_time_path):
    """
    Create a graph weighted by travel times.
    
    Args:
        base_graph_path (str): Path to the original GraphML file.
        travel_time_path (str): Path to the travel time data.
    
    Returns:
        networkx.Graph: Graph weighted by travel times
    """
    # Load the base graph
    G = ox.load_graphml(base_graph_path)
    
    # Load travel time data
    with open(travel_time_path, 'r') as f:
        travel_time_data = json.load(f)
    
    # Create a new graph weighted by travel times
    G_time = G.copy()
    
    # Update edge weights
    for u, v, data in G_time.edges(data=True):
        edge_id = f"{u},{v}"
        if edge_id in travel_time_data["edges"]:
            data['weight'] = travel_time_data["edges"][edge_id]["travel_time"]
        else:
            # If we don't have travel time data, use a default based on length
            data['weight'] = float(data.get('length', 0)) / 30  # Assume 30 km/h
    
    return G_time

if __name__ == "__main__":
    # Example usage
    graph_path = "../data/road_network.graphml"
    travel_time_path = "../data/travel_times.json"
    
    # Calculate and save travel times
    G_updated = calculate_travel_times(graph_path, travel_time_path)
    
    # Create time-weighted graph
    G_time = create_time_weighted_graph(graph_path, travel_time_path)
    
    # Save time-weighted graph
    time_graph_path = "../data/road_network_time_weighted.graphml"
    ox.save_graphml(G_time, time_graph_path)
    print(f"Time-weighted graph saved at {time_graph_path}")