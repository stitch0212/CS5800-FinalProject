# Consider only sun exposure

import osmnx as ox
import json
from geopy.distance import geodesic

def integrate_noaa_data(graph_path, solar_data_path, output_path):
    """
    Integrate NOAA solar data into the road network graph.

    Args:
        graph_path (str): Path to the road network GraphML file.
        solar_data_path (str): Path to the NOAA solar data JSON file.
        output_path (str): Path to save the updated GraphML file.
    """
    print("Loading road network graph...")
    G = ox.load_graphml(graph_path)

    print("Loading NOAA solar data...")
    with open(solar_data_path, "r") as f:
        solar_data = json.load(f)

    # Extract solar data points (lat, lon, exposure)
    solar_points = []
    for point in solar_data.get("outputs", {}).get("solar_resource", []):
        solar_points.append({
            "lat": point["lat"],
            "lon": point["lon"],
            "solar_exposure": point["ghi"]  # Global Horizontal Irradiance
        })

    def map_solar_to_road(u, v, data, solar_points):
        """
        Map solar exposure to a road segment based on proximity.

        Args:
            u, v: Nodes of the edge.
            data (dict): Edge data (e.g., geometry, length).
            solar_points (list): List of solar data points with lat, lon, and exposure.

        Returns:
            float: Solar exposure value for the road segment.
        """
        if "geometry" not in data:
            return 1  # Default exposure if no geometry exists

        # Get road segment midpoint
        coords = list(data["geometry"].coords)
        midpoint = coords[len(coords) // 2]

        # Find closest solar point to the midpoint
        closest_exposure = 1  # Default exposure
        min_distance = float("inf")
        for point in solar_points:
            distance = geodesic(midpoint, (point["lat"], point["lon"])).meters
            if distance < min_distance:
                min_distance = distance
                closest_exposure = point["solar_exposure"]

        return closest_exposure

    print("Integrating solar data into the road network...")
    for u, v, key, data in G.edges(data=True, keys=True):
        data["solar_exposure"] = map_solar_to_road(u, v, data, solar_points)
        data["weight"] = float(data.get("length", 1)) / max(float(data.get("solar_exposure", 1)), 0.1)

    print("Saving updated road network graph...")
    ox.save_graphml(G, output_path)
    print(f"Updated graph saved at {output_path}")

if __name__ == "__main__":
    graph_path = "../data/road_network.graphml"
    solar_data_path = "../data/solar_data.json"
    output_path = "../data/updated_road_network.graphml"

    integrate_noaa_data(graph_path, solar_data_path, output_path)