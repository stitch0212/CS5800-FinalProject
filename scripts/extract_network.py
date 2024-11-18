import osmnx as ox

def extract_road_network(location, save_path):
    # Download road network
    G = ox.graph_from_place(location, network_type="drive")
    # Save as a GraphML file for future use
    ox.save_graphml(G, filepath=save_path)
    print(f"Road network saved at {save_path}")

if __name__ == "__main__":
    location = "Vancouver, British Columbia, Canada"
    save_path = "../data/road_network.graphml"
    extract_road_network(location, save_path)