def map_to_pixel(point, map_bounds, image_size):
    """
    Map a geographic point to a pixel on the image.
    :param point: Shapely Point (longitude, latitude).
    :param map_bounds: Bounds of the map (min_lon, min_lat, max_lon, max_lat).
    :param image_size: Size of the shadow map (width, height).
    :return: (x, y) pixel coordinates.
    """
    min_lon, min_lat, max_lon, max_lat = map_bounds
    width, height = image_size
    x = int((point.x - min_lon) / (max_lon - min_lon) * width)
    y = int((point.y - min_lat) / (max_lat - min_lat) * height)
    return x, y

def calculate_shade_coverage(road_pixels, shadow_mask, image_size):
    """
    Calculate the percentage of the road covered by shade.
    :param road_pixels: List of (x, y) pixel coordinates for the road.
    :param shadow_mask: 2D array of boolean values (True for shaded, False otherwise).
    :param image_size: Tuple (width, height) of the shadow map.
    :return: Percentage of the road covered by shade.
    """
    shaded_points = sum(
        shadow_mask[y, x]
        for x, y in road_pixels
        if 0 <= x < image_size[0] and 0 <= y < image_size[1]
    )
    total_points = len(road_pixels)
    return (shaded_points / total_points) * 100
