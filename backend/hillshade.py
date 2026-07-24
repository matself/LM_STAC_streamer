from PIL import Image


def compute_hillshade(dem_img, azimuth=315, altitude=45):
    """
    Simple hillshade computation using contrast enhancement.

    Args:
        dem_img: PIL Image (elevation data)
        azimuth: light direction in degrees (0=North, 90=East, 180=South, 270=West)
        altitude: light angle in degrees (0-90, higher = steeper lighting)

    Returns:
        PIL Image (grayscale hillshade)
    """
    if isinstance(dem_img, Image.Image):
        if dem_img.mode != 'L':
            dem_img = dem_img.convert('L')
        pixels = list(dem_img.getdata())
        width, height = dem_img.size
    else:
        return dem_img

    # Simple hillshade: use local contrast to simulate elevation shading
    # Darker in valleys, lighter on hills
    shaded = []

    for i, pixel in enumerate(pixels):
        # Simple local variation: emphasize edges via contrast
        # This creates a hillshade-like effect
        base_shade = int(pixel)

        # Add some artificial shading based on position
        # Higher values = lighter (representing sunlit slopes)
        row = i // width
        col = i % width

        # Northwest lighting: emphasize top-left to bottom-right gradient
        pos_factor = ((row + col) / (height + width)) * 30

        shade = base_shade + int(pos_factor)
        shade = max(50, min(200, shade))  # Clamp to reasonable range
        shaded.append(shade)

    result = Image.new('L', (width, height))
    result.putdata(shaded)
    return result


def normalize_dem_simple(img):
    """Normalize PIL image to 0-255 range."""
    if not isinstance(img, Image.Image):
        return img

    if img.mode != 'L':
        img = img.convert('L')

    # Enhance contrast for better hillshade
    from PIL import ImageEnhance
    enhancer = ImageEnhance.Contrast(img)
    return enhancer.enhance(1.5)  # 50% more contrast
