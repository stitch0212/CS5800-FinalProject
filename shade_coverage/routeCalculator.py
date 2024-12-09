import networkx as nx
import geopandas as gpd
import json

def get_street_name_by_nodes(geojson_data, u, v):
    """
    Extract unique street names for a given pair of nodes (u, v) from the GeoJSON data.

    Parameters:
    - geojson_data (dict): Loaded GeoJSON data as a dictionary.
    - u (int): Start node ID.
    - v (int): End node ID.

    Returns:
    - str: A single unique street name or a comma-separated list of unique street names.
    """
    street_names = set()  # Use a set to store unique street names

    # Iterate through features to find matching u and v
    for feature in geojson_data['features']:
        props = feature['properties']
        if props['u'] == u and props['v'] == v:
            name = props.get('name', 'Unknown Street')  # Get the name or default to 'Unknown Street'

            # Handle cases where name is a list
            if isinstance(name, list):
                for sub_name in name:  # Add each name in the list to the set
                    if sub_name:  # Ensure sub_name is not None or empty
                        street_names.add(sub_name)
            elif name:  # Handle single names
                street_names.add(name)

    # Return a single name if there's only one, or join multiple names with commas
    if not street_names:
        return 'Unknown Street'  # If no names found, return default
    return ', '.join(str(name) for name in street_names)  # Convert all names to strings and join



def build_graph_from_data(file_path):
    """
    Constructs a graph from a GeoJSON file with road and shade data.

    Parameters:
    - file_path (str): Path to the GeoJSON file containing roads with shade data.

    Returns:
    - graph (networkx.DiGraph): A directed graph where nodes are junctions and edges are road segments.
    """
    # Load the data
    roads_with_shade = gpd.read_file(file_path)
    with open(file_path, 'r') as f:
        geojson_data = json.load(f)

    # Initialize a directed graph
    graph = nx.DiGraph()

    # Keep track of added edges to avoid duplicates
    added_edges = set()

    # Add edges with weights and street names to the graph
    for _, row in roads_with_shade.iterrows():
        u = row['u']  # Start junction
        v = row['v']  # End junction

        # Create a tuple to uniquely identify the edge
        edge_key = (u, v)
        if edge_key in added_edges:
            continue  # Skip if the edge is already added

        # Get the street name for this edge
        street_name = get_street_name_by_nodes(geojson_data, u, v)

        # Add the edge to the graph with additional attributes
        graph.add_edge(u, v, weight=1, street_name=street_name)

        # Mark this edge as added
        added_edges.add(edge_key)

    return graph

def find_most_uncovered_route_with_streets(graph, start, end):
    """
    Finds the route with the least shade coverage between two points, including street names.

    Parameters:
    - graph (networkx.DiGraph): The road network graph.
    - start (int): Starting junction node ID.
    - end (int): Ending junction node ID.

    Returns:
    - path (list): The list of nodes representing the route.
    - total_weight (float): The total weight of the path (measure of uncoveredness).
    - street_names (list): List of street names along the path.
    """
    try:
        # Find the shortest path
        path = nx.shortest_path(graph, source=start, target=end, weight='weight')
        total_weight = nx.shortest_path_length(graph, source=start, target=end, weight='weight')

        # Map edges in the path to street names
        street_names = []
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            street_name = graph[u][v].get('street_name', 'Unknown Street')
            street_names.append(street_name)

        return path, total_weight, street_names
    except nx.NetworkXNoPath:
        return None, float('inf'), []

# Example Usage
if __name__ == "__main__":
    # File path to the GeoJSON file
    file_path = "data/road_geometry.geojson"  # Update this path as necessary

    # Build the graph
    graph = build_graph_from_data(file_path)

    # Define start and end nodes
    start_node = 25251472  # Example starting node
    end_node = 244085837  # Example ending node

    # Find the most-uncovered route
    path, total_weight, street_names = find_most_uncovered_route_with_streets(graph, start_node, end_node)

    if path:
        print("Most-Uncovered Route (Nodes):", path)
        print("Total Uncoveredness Score:", total_weight)
        print("Street Names on Route:", street_names)
    else:
        print("No path found between the given points.")

