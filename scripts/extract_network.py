import osmnx as ox
import logging
from pathlib import Path

def extract_road_network(location, output_path):
    """
    Extract the road network for the specified location and save it as a GraphML file.

    Args:
        location (str): The location name (e.g., "Vancouver, British Columbia, Canada").
        output_path (str): The file path to save the GraphML file.
    """
    try:
        # Create output directory if it doesn't exist
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Download the road network for driving
        print(f"Extracting road network for {location}...")
        G = ox.graph_from_place(location, network_type="drive")
        
        # Add basic attributes we'll need later
        for _, _, data in G.edges(data=True):
            data['solar_exposure'] = 0.0  # Will be updated later
            data['travel_time'] = 0.0     # Will be updated later
            
        print("Graph extracted successfully.")

        # Save the graph as a GraphML file
        ox.save_graphml(G, output_path)
        print(f"Road network saved at {output_path}")
        
        return G
        
    except Exception as e:
        print(f"Error extracting road network: {str(e)}")
        raise

if __name__ == "__main__":
    # Example usage
    location = "Vancouver, British Columbia, Canada"
    output_path = "../data/road_network.graphml"
    extract_road_network(location, output_path)