import osmnx as ox
from scripts.optimize_route import greedy_route, dp_route
from scripts.visualize_route import visualize_route
import matplotlib.pyplot as plt
import networkx as nx

def main():
    # Load the updated road network graph
    print("Loading the road network graph...")
    graph_path = "./data/updated_road_network.graphml"
    G = ox.load_graphml(graph_path)
    '''
    # Check if the graph is strongly connected
    if not nx.is_strongly_connected(G):
      print("The graph is not strongly connected. Using the largest weakly connected component.")
      G = G.subgraph(max(nx.weakly_connected_components(G), key=len)).copy()
      print(f"Graph size after filtering: {len(G.nodes)} nodes, {len(G.edges)} edges.")
  '''

    # Define start and end nodes (replace with actual node IDs or coordinates)
    print("Defining start and end nodes...")
    start_lat, start_lon = 49.2886292, -123.1384087
    end_lat, end_lon = 49.2098464, -123.115616


    # Find the nearest nodes in the projected graph
    print("Finding the nearest nodes for start and end points...")
    start_node = ox.nearest_nodes(G, X=start_lon, Y=start_lat)
    end_node = ox.nearest_nodes(G, X=end_lon, Y=end_lat)
    print(f"Start node: {start_node}, End node: {end_node}")

    '''
    # Run Greedy Algorithm
    print("Running Greedy Algorithm...")
    greedy_path = greedy_route(G, start_node, end_node)
    print(f"Greedy Path: {greedy_path}")
    '''

    # Run DP (Dijkstra) Algorithm
    print("Running DP (Dijkstra's Algorithm)...")
    dp_path = dp_route(G, start_node, end_node)
    print(f"DP Path: {dp_path}")

    # Visualize the results
    print("Visualizing the routes...")
    # visualize_route(G, greedy_path, "./results/greedy_route.png", "Greedy Algorithm Route")
    visualize_route(G, dp_path, "./results/dp_route.png", "DP (Dijkstra) Algorithm Route")

if __name__ == "__main__":
    main()
