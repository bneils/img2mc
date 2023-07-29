import numpy as np
from PIL import Image, features
from PIL.Image import Quantize, Dither
from math import ceil
from nbt.nbt import *

MAP_RESOLUTION = 128
TRANSPARENT_START = 0 # Taken from the wiki
TRANSPARENT_END_EXCL = 4 # 3 channels, 4 shades

_quantize_method_names = {
    "off": Quantize.MEDIANCUT,
    "median-cut": Quantize.MEDIANCUT,
    "max-coverage": Quantize.MAXCOVERAGE,
    "fast-octree": Quantize.FASTOCTREE,
    "libimagequant": Quantize.LIBIMAGEQUANT,
}

def get_palette_num_colors(palette_image):
    return len(palette_image.getpalette()) // 3

def partition_image_to_map_items(
    image, palette_image, scale_settings=(1, 1), quantize_method="median-cut",
    alpha_threshold=128, transparency_color=TRANSPARENT_START):
    """Returns a list of tuples containing linear map ids and alpha values"""

    # Check args
    if len(scale_settings) != 2:
        raise ValueError("scale must be a 2-element vector")

    # We need opacity to determine transparency
    image = image.convert("RGBA")

    # A copy is made so that the original data isn't modified
    # This is important for GIFs where the parameter will be used more than
    # once.
    scale_settings = list(scale_settings).copy()

    if scale_settings[0] is None or scale_settings[1] is None:
        if scale_settings[0] is None:
            #  Scale the image to ?:H maps and keep the ratio
            #   - It is also centered left-right
            height = scale_settings[1] * MAP_RESOLUTION
            wh_ratio = image.width / image.height
            width = int(wh_ratio * height)

            scale_settings[0] = ceil(wh_ratio * scale_settings[1])
            left_padding = int((scale_settings[0] * MAP_RESOLUTION - width) / 2)
            top_padding = 0
        elif scale_settings[1] is None:
            #  Scale the image to W:? maps and keep the ratio
            #   - It is also centered top-down
            width = scale_settings[0] * MAP_RESOLUTION
            hw_ratio = image.height / image.width
            height = int(hw_ratio * width)

            scale_settings[1] = ceil(hw_ratio * scale_settings[0])
            left_padding = 0
            top_padding = int((scale_settings[1] * MAP_RESOLUTION - height) / 2)
        else:
            raise ValueError("not possible")

        # I don't use the size previously calculated because I want the size of
        # the canvas, not the image being fit to it
        canvas_size = (scale_settings[0] * MAP_RESOLUTION,
                       scale_settings[1] * MAP_RESOLUTION)
        new_im = Image.new('RGBA', canvas_size)

        new_im.paste(image.resize((width, height)), (left_padding, top_padding))
        image = new_im
    else:
        # Scale the image to W:H maps and (potentially) break the ratio
        canvas_size = (scale_settings[0] * MAP_RESOLUTION,
                       scale_settings[1] * MAP_RESOLUTION)
        image = image.resize(canvas_size)

    # Convert user input to parameters for PIL.quantize
    dither = Dither.NONE if quantize_method == "off" else Dither.FLOYDSTEINBERG
    method = _quantize_method_names[quantize_method]

    if method == Quantize.LIBIMAGEQUANT and not \
        features.check_feature("libimagequant"):
        raise ValueError("Your environment likely does not support " +
                         "libimagequant.")

    # Put pixels into rows and columns for easy partitioning
    map_ids = np.asarray(image.convert('RGB').quantize(palette=palette_image,
        colors=get_palette_num_colors(palette_image), dither=dither,
        method=method)) + TRANSPARENT_END_EXCL
    map_ids = np.ravel(map_ids)

    # Perform some masking using the alpha threshold
    alphas = np.asarray(image.getdata(3))
    map_id_alpha_pairs = np.dstack((map_ids, alphas))[0]
    map_id_alpha_pairs[alphas <= alpha_threshold, 0] = transparency_color
    map_ids = map_id_alpha_pairs[:, 0].reshape(image.size[::-1])

    # Split the map id matrix into smaller 128x128 squares
    return [
        map_ids[y:y + 128, x:x + 128].reshape(128 * 128)
        for y in range(0, image.height, 128)
        for x in range(0, image.width, 128)
    ]


def create_map(map_color_ids):
    # Begin constructing the NBT file described at
    # https://minecraft.gamepedia.com/Map_item_format#map_.3C.23.3E.dat_format
    map_color_ids = list(map_color_ids)

    nbt_file = NBTFile()
    nbt_file.name = "root"

    data = TAG_Compound()
    data.name = "data"  # only works if on a separate line
    nbt_file.tags.append(data)
    
    data.tags.extend([
        TAG_Byte(name = "scale", value = 0),
        TAG_Byte(name = "dimension", value = 0),
        TAG_Byte(name = "locked", value = 1),
        TAG_Byte(name = "trackingPosition", value = 0),
        TAG_Int(name = "xCenter", value = 0),
        TAG_Int(name = "zCenter", value = 0),
        TAG_Short(name = "height", value = 128),
        TAG_Short(name = "width", value = 128),
    ])

    # Load image data
    image_data = TAG_Byte_Array(name = "colors")
    image_data.value = map_color_ids
    data.tags.append(image_data)
    return nbt_file
