import osmnx as ox

def extract_road_network(location, output_path):
    """
    Extract the road network for the specified location and save it as a GraphML file.

    Args:
        location (str): The location name (e.g., "Vancouver, British Columbia, Canada").
        output_path (str): The file path to save the GraphML file.
    """
    # Download the road network for driving
    print(f"Extracting road network for {location}...")
    G = ox.graph_from_place(location, network_type="drive")
    print("Graph extracted successfully.")

    # Save the graph as a GraphML file
    ox.save_graphml(G, output_path)
    print(f"Road network saved at {output_path}")

if __name__ == "__main__":
    # Example usage
    location = "Vancouver, British Columbia, Canada"
    output_path = "../data/road_network.graphml"
    extract_road_network(location, output_path)
