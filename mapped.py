#!/usr/bin/env python3
# Made by Ben Neilsen
# Created: 6/3/20

from colormath.color_diff_matrix import delta_e_cie1976 as delta_e
from colormath.color_objects import LabColor, sRGBColor
from colormath.color_conversions import convert_color
from PIL import Image
from nbt.nbt import *
from numpy import array, argmin
from argparse import ArgumentParser
from json import load

import os, sys

with open('lab_colors.json') as f:
    lab_colors = load(f)


def mapnbt(image):
    # Minecraft maps must fit in a 128x128 pixel area
    image = image.resize((128, 128), Image.LANCZOS)

    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    alpha_channel = image.getchannel(3).getdata()
    image = image.convert('P')
    
    palette = array(image.getpalette()).reshape(256, 3)

    index_to_id = [argmin(delta_e(array(convert_color(sRGBColor(*rgb), LabColor).get_value_tuple()),
			lab_colors)) + 4
                    for rgb in palette]

    # Collect a list of map color ids by finding the closest color's indice (4 is added due to the absent transparent values at 0-3)
    mapColorIds = [index_to_id[index] if alpha else 0 for index, alpha in zip(image.getdata(), alpha_channel)]

    # Begin constructing the NBT file at https://minecraft.gamepedia.com/Map_item_format#map_.3C.23.3E.dat_format
    nbtfile = NBTFile()
    nbtfile.name = "root"

    data = TAG_Compound()
    data.name = "data"  # only works if on a separate line
    nbtfile.tags.append(data)
    
    data.tags.extend([
        TAG_Byte(name = "scale", value = 0),
        TAG_Byte(name = "dimension", value = 0),
        TAG_Byte(name = "locked", value = 1),
        TAG_Byte(name = "trackingPosition", value = 0),
        TAG_Int(name = "xCenter", value = 0),
        TAG_Int(name = "zCenter", value = 0),
        TAG_Short(name = "height", value = 128),
        TAG_Short(name = "width", value = 128)
    ])

    # Load image data
    imageData = TAG_Byte_Array(name = "colors")
    imageData.value = mapColorIds
    data.tags.append(imageData)

    return nbtfile


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('fp', metavar='path', help='the file path of the image')
    parser.add_argument('num', metavar='map-#', type=int, help='how many maps exist in your world.')
    parser.add_argument('-d', '--dir', metavar='dir', default='.', help="the directory to save in. Defaults to working directory.")

    args = parser.parse_args()

    try:
        image = Image.open(args.fp)
    except FileNotFoundError as e:
        sys.exit(e)
    
    nbtfile = mapnbt(image)

    try:
        nbtfile.write_file(os.path.join(args.dir,'map_%d.dat' % args.num))
    except FileNotFoundError as e:
        sys.exit(e)
