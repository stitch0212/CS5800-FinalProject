import networkx as nx
import osmnx as ox
import heapq
import time


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
    path = [source]
    current = source
    visited = set()  # Track visited nodes
    start_time = time.time()

    while current != target:
        if current in visited:
            raise ValueError(f"Cycle detected: Node {current} was revisited.")
        visited.add(current)

        # Get neighbors with weights, excluding already visited nodes
        neighbors = []
        for v in G.neighbors(current):
            if v not in visited:  # Exclude visited nodes
                for key, edge_data in G[current][v].items():
                    if "weight" in edge_data:
                        neighbors.append((v, float(edge_data["weight"])))

        if not neighbors:
            raise ValueError(f"No valid neighbors for node {current}. The graph may be disconnected.")

        # Sort neighbors by weight (ascending order)
        neighbors.sort(key=lambda x: x[1])
        next_node = neighbors[0][0]

        print(f"Current node: {current}, Next node: {next_node}, Elapsed time: {time.time() - start_time:.2f}s")

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
    # Initialize distances and priority queue
    dp = {node: float("inf") for node in G.nodes}
    dp[source] = 0
    pq = [(0, source)]  # Priority queue: (cost, node)
    prev = {}

    while pq:
        current_cost, current_node = heapq.heappop(pq)

        # Exit if the target is reached
        if current_node == target:
            break

        # Iterate over neighbors
        for neighbor in G.neighbors(current_node):
            for key, edge_data in G[current_node][neighbor].items():
                if "weight" in edge_data:
                    weight = float(edge_data["weight"])
                    new_cost = current_cost + weight

                    if new_cost < dp[neighbor]:
                        dp[neighbor] = new_cost
                        prev[neighbor] = current_node
                        heapq.heappush(pq, (new_cost, neighbor))

    # Reconstruct the path
    if target not in prev:
        print("No path found between source and target.")
        return []

    path = []
    node = target
    while node in prev:
        path.append(node)
        node = prev[node]
    path.append(source)
    path.reverse()

    return path
