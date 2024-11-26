import osmnx as ox
import matplotlib.pyplot as plt
import contextily as ctx
import networkx as nx

def visualize_route(G, route, output_path=None, title="Route with Features"):
    """
    Visualize a route with additional features such as a basemap and road context.

    Args:
        G (Graph): The road network graph.
        route (list): List of node IDs representing the route.
        output_path (str): File path to save the visualization (optional).
        title (str): Title of the visualization plot.
    """
    print("Visualizing the route with additional features...")

    try:
        # Get graph nodes and edges
        nodes, edges = ox.graph_to_gdfs(G)

        # Plot the graph
        fig, ax = plt.subplots(figsize=(12, 12))
        edges.plot(ax=ax, linewidth=0.5, edgecolor="gray", alpha=0.5, label="Roads")

        # Highlight the route
        route_edges = [(u, v) for u, v in zip(route[:-1], route[1:])]
        nx.draw_networkx_edges(
            G,
            pos={node: (data["x"], data["y"]) for node, data in G.nodes(data=True)},
            edgelist=route_edges,
            edge_color="red",
            width=2,
            ax=ax,
            label="Route",
        )

        # Add start and end nodes
        start_node, end_node = route[0], route[-1]
        start_coords = (G.nodes[start_node]["x"], G.nodes[start_node]["y"])
        end_coords = (G.nodes[end_node]["x"], G.nodes[end_node]["y"])
        ax.scatter(*start_coords, color="green", s=100, label="Start")
        ax.scatter(*end_coords, color="blue", s=100, label="End")

        # Add basemap
        ctx.add_basemap(
            ax,
            crs=edges.crs,
            source=ctx.providers.OpenStreetMap.Mapnik
        )

        # Add a legend
        ax.legend(loc="upper left")

        # Add a title
        ax.set_title(title, fontsize=16)

        # Save the visualization if needed
        if output_path:
            print(f"Saving visualization to {output_path}...")
            fig.savefig(output_path, bbox_inches="tight", dpi=300)
            print(f"Visualization saved at {output_path}")

        # Show the plot
        plt.show()

    except Exception as e:
        print(f"Error during visualization: {str(e)}")
        raise
