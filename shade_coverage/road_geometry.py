import osmnx as ox
import geopandas as gpd
import os

def load_road_geometry(place_name: str, output_path: str = "data/road_geometry.geojson"):
    """
    Fetches road geometry for a given place and saves it as a GeoJSON file.

    Args:
        place_name (str): The name of the place to fetch road geometry for (e.g., "Vancouver, Canada").
        output_path (str): Path to save the GeoJSON file.
    
    Returns:
        gpd.GeoDataFrame: A GeoDataFrame containing the road geometry.
    """
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Fetch road geometry
    print(f"Fetching road geometry for {place_name}...")
    graph = ox.graph_from_place(place_name, network_type="drive")

    # Convert to GeoDataFrame
    gdf_nodes, gdf_edges = ox.graph_to_gdfs(graph)

    # Save edges (road geometry) as GeoJSON
    gdf_edges.to_file(output_path, driver="GeoJSON")
    print(f"Road geometry saved to {output_path}")

    return gdf_edges

