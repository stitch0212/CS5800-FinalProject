import osmnx as ox
import matplotlib.pyplot as plt

def visualize_route(G, route, output_path=None, title="Route Visualization"):
    """
    Visualize a route on the road network graph.

    Args:
        G (Graph): The road network graph.
        route (list): List of node IDs representing the route.
        output_path (str): File path to save the visualization (optional).
        title (str): Title of the visualization plot.
    """
    print("Visualizing the route...")

    # Plot the graph and the route
    fig, ax = ox.plot_graph_route(
        G,
        route,
        route_color="red",  # Color of the route
        route_linewidth=2,  # Width of the route line
        node_size=10,       # Size of the nodes
        bgcolor="white",    # Background color
        show=False          # Do not show the plot immediately
    )

    # Add a title to the plot
    ax.set_title(title, fontsize=14)

    # Save the visualization if an output path is provided
    if output_path:
        print(f"Saving visualization to {output_path}...")
        fig.savefig(output_path, bbox_inches="tight", dpi=300)
        print(f"Visualization saved at {output_path}")

    # Show the plot
    plt.show()
