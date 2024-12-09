from PIL import Image
import numpy as np

def generate_shadow_mask(image_path, threshold=128):
    """
    Generate a binary shadow mask from a shadow map.
    :param image_path: Path to the shadow map PNG file.
    :param threshold: Intensity threshold for shadow classification.
    :return: (shadow_mask, image_size)
    """
    shadow_map = Image.open(image_path).convert("L")  # Convert to grayscale
    shadow_array = np.array(shadow_map)
    shadow_mask = shadow_array < threshold  # True for shadowed pixels
    return shadow_mask, shadow_array.shape[::-1]  # Return mask and (width, height)
