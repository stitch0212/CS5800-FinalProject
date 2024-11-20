import networkx as nx
import osmnx as ox

def greedy_route(G, source, target):
    """
    Find a route from source to target using a greedy approach.

    Args:
        G (Graph): The road network graph.
        source (node): Starting node in the graph.
        target (node): Destination node in the graph.

    Returns:
        list: A list of nodes representing the path from source to target.
    """
    path = [source]  # Initialize path with the source node
    current = source  # Start at the source node

    while current != target:
        # Get all neighbors of the current node along with their weights
        # Access multi-edge attributes
        neighbors = []
        for v in G.neighbors(current):
            for key, edge_data in G[current][v].items():  # Iterate over multi-edge attributes
                if "weight" in edge_data:
                    neighbors.append((v, float(edge_data["weight"])))


        # Sort neighbors by weight (ascending order)
        neighbors.sort(key=lambda x: x[1])

        # Select the neighbor with the smallest weight
        next_node = neighbors[0][0]

        # Add the selected neighbor to the path and move to it
        path.append(next_node)
        current = next_node

    return path

def dp_route(G, source, target):
    """
    Find the shortest path from source to target using dynamic programming (Dijkstra's algorithm).

    Args:
        G (Graph): The road network graph.
        source (node): Starting node in the graph.
        target (node): Destination node in the graph.

    Returns:
        list: A list of nodes representing the shortest path from source to target.
    """
    import heapq

    # Initialize distances to all nodes as infinity, except for the source node
    dp = {node: float("inf") for node in G.nodes}
    dp[source] = 0  # Distance to the source node is 0

    # Priority queue for selecting the next node with the smallest cost
    pq = [(0, source)]  # (cost, node)

    # Dictionary to keep track of the previous node for path reconstruction
    prev = {}

    while pq:
        # Extract the node with the smallest cost from the priority queue
        current_cost, current_node = heapq.heappop(pq)

        # If the target node is reached, exit the loop
        if current_node == target:
            break

        # Iterate over all neighbors of the current node
        for neighbor in G.neighbors(current_node):
            weight = G[current_node][neighbor]["weight"]  # Get the edge weight
            new_cost = current_cost + weight  # Calculate the new cost to reach the neighbor

            # If the new cost is better than the currently recorded cost
            if new_cost < dp[neighbor]:
                dp[neighbor] = new_cost  # Update the cost to reach the neighbor
                prev[neighbor] = current_node  # Update the previous node for the neighbor
                heapq.heappush(pq, (new_cost, neighbor))  # Add the neighbor to the priority queue

    # Reconstruct the shortest path from the source to the target
    path = []
    node = target
    while node in prev:
        path.append(node)  # Add the current node to the path
        node = prev[node]  # Move to the previous node
    path.append(source)  # Add the source node to the path
    path.reverse()  # Reverse the path to get the correct order from source to target

    return path
