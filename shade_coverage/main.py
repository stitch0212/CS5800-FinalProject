from road_geometry import load_road_geometry
import geopandas as gpd
import numpy as np
from PIL import Image
from shapely.geometry import mapping
import rasterio
import rasterio.features
from rasterio.transform import from_bounds

def calculate_shade_coverage(roads: gpd.GeoDataFrame, shadow_map_path: str) -> gpd.GeoDataFrame:
    """
    Calculates the percentage of each road segment covered by shade.

    Args:
        roads (gpd.GeoDataFrame): GeoDataFrame containing road geometry.
        shadow_map_path (str): Path to the shadow map PNG file.

    Returns:
        gpd.GeoDataFrame: Updated GeoDataFrame with a new column 'shade_percentage'.
    """
 

    # Load the shadow map as a binary mask
    print(f"Loading shadow map from {shadow_map_path}...")
    shadow_image = Image.open(shadow_map_path).convert("L")
    shadow_array = np.array(shadow_image)

    threshold = 128
    shadow_mask = shadow_array < threshold

    # Define the bounds and resolution of the shadow map
    map_width, map_height = shadow_image.size
    xmin, ymin, xmax, ymax = roads.total_bounds  # Bounding box of all roads
    transform = from_bounds(xmin, ymin, xmax, ymax, map_width, map_height)

    # Function to calculate coverage for each road
    def compute_coverage(geometry):
        if geometry.is_empty:
            return 0.0

        # Rasterize the geometry onto the shadow map
        shapes = [mapping(geometry)]
        rasterized = rasterio.features.rasterize(
            shapes,
            out_shape=(map_height, map_width),
            transform=transform,
            fill=0,
            dtype=np.uint8
        )

        # Compare rasterized road pixels with the shadow mask
        shaded_pixels = np.sum((rasterized == 1) & shadow_mask)
        total_pixels = np.sum(rasterized == 1)

        # Calculate the percentage of road that is shaded
        return (shaded_pixels / total_pixels) * 100 if total_pixels > 0 else 0.0

    # Apply the coverage calculation to each road
    print("Calculating shade coverage for each road...")
    roads["shade_percentage"] = roads["geometry"].apply(compute_coverage)

    return roads


def main():
    # Define paths and inputs
    place_name = "Vancouver, Canada"
    road_geometry_path = "data/road_geometry.geojson"
    shadow_map_path = "data/shadow_map.png" 

    # Step 1: Load or Fetch Road Geometry
    try:
        roads = load_road_geometry(place_name, road_geometry_path)
    except Exception as e:
        print(f"Error loading road geometry: {e}")
        return

    # Step 2: Calculate Shade Coverage
    try:
        roads_with_shade = calculate_shade_coverage(roads, shadow_map_path)
        print("Shade coverage calculation complete.")
        print(roads_with_shade[["geometry", "shade_percentage"]].head())  # Preview results
    except Exception as e:
        print(f"Error calculating shade coverage: {e}")
        return

    # Step 3: Save the Results
    output_path = "data/roads_with_shade.geojson"
    roads_with_shade.to_file(output_path, driver="GeoJSON")
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    main()


