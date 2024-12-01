import osmnx as ox
import matplotlib.pyplot as plt
import contextily as ctx
import networkx as nx

def visualize_route(G, route, output_path=None, title="Route Visualization"):
    """
    Visualize a route with a focused map view and accurate road alignment.

    Args:
        G (Graph): The road network graph.
        route (list): List of node IDs representing the route.
        output_path (str): File path to save the visualization (optional).
        title (str): Title of the visualization plot.
    """
    print("Visualizing the route with improved alignment...")

    try:
        # Get start and end nodes
        start_node, end_node = route[0], route[-1]
        start_coords = (G.nodes[start_node]["x"], G.nodes[start_node]["y"])
        end_coords = (G.nodes[end_node]["x"], G.nodes[end_node]["y"])

        # Calculate the bounding box for the route
        min_x = min(start_coords[0], end_coords[0])
        min_y = min(start_coords[1], end_coords[1])
        max_x = max(start_coords[0], end_coords[0])
        max_y = max(start_coords[1], end_coords[1])

        # Expand the bounding box slightly
        buffer_percent = 0.1
        x_buffer = (max_x - min_x) * buffer_percent
        y_buffer = (max_y - min_y) * buffer_percent
        min_x -= x_buffer
        min_y -= y_buffer
        max_x += x_buffer
        max_y += y_buffer

        # Plot the route
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.set_xlim(min_x, max_x)
        ax.set_ylim(min_y, max_y)

        # Draw the roads
        for u, v, data in G.edges(data=True):
            if 'geometry' in data:
                xs, ys = zip(*data['geometry'].coords)
                ax.plot(xs, ys, color='gray', linewidth=1)
            else:
                # If 'geometry' is not available, draw a straight line between nodes
                node_u = (G.nodes[u]['x'], G.nodes[u]['y'])
                node_v = (G.nodes[v]['x'], G.nodes[v]['y'])
                ax.plot([node_u[0], node_v[0]], [node_u[1], node_v[1]], color='gray', linewidth=1)

        # Draw the route
        for u, v in zip(route[:-1], route[1:]):
            if (u, v) in G.edges:
                edge_data = G.edges[u, v, 0]
                if 'geometry' in edge_data:
                    xs, ys = zip(*edge_data['geometry'].coords)
                    ax.plot(xs, ys, color='red', linewidth=2)
                else:
                    # If 'geometry' is not available, draw a straight line between nodes
                    node_u = (G.nodes[u]['x'], G.nodes[u]['y'])
                    node_v = (G.nodes[v]['x'], G.nodes[v]['y'])
                    ax.plot([node_u[0], node_v[0]], [node_u[1], node_v[1]], color='red', linewidth=2)

        # Draw start and end points
        ax.scatter(*start_coords, color="green", s=100, label="Start")
        ax.scatter(*end_coords, color="blue", s=100, label="End")

        # Add a basemap
        ctx.add_basemap(
            ax,
            crs=G.graph["crs"],
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

    except Exception as e:
        print(f"Error during visualization: {str(e)}")
        raise