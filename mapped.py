#!/usr/bin/env python3
__author__ = "Ben Neilsen"

from PIL import Image, ImageSequence
from PIL.Image import Dither, Quantize
from argparse import ArgumentParser
from tqdm import tqdm
import os
import sys

from helper import *

TRANSPARENT_START = 0 # Taken from the wiki
TRANSPARENT_END_EXCL = 4 # 3 channels, 4 shades

def hex_color_to_tuple(color: str):
    if color[0] == "#":
        color = color[1:]
    r, g, b = color[:2], color[2:4], color[4:6]
    return (int(r, base=16), int(g, base=16), int(b, base=16))

def match_color(color, palette_image):
    pix = Image.new("RGB", (1, 1), color=color)
    quant_pix = pix.quantize(palette=palette_image,
                             colors=get_palette_num_colors(palette_image),
                             dither=Dither.NONE)
    return list(quant_pix.getdata())[0]

def load_palette():
    script_dir = os.path.dirname(os.path.realpath(sys.argv[0]))

    with open(os.path.join(script_dir, "dev-tools/palette.csv"), "r") as f:
        channels = [int(num) for num in f.read().split(",")]
        # Truncate the beginning transparency section from the palette
        channels = channels[TRANSPARENT_END_EXCL * 3:]
        # The palette image is a blank image that will act as
        # a surrogate for the palette
        palette_image = Image.new('P', (0, 0))
        palette_image.putpalette(channels)
    return palette_image

def matched_color_to_map_color(color, alpha, alpha_threshold,
                               override_transparency=None):
    if alpha < alpha_threshold:
        return TRANSPARENT_START if not override_transparency else \
            override_transparency + TRANSPARENT_END_EXCL
    # This adjustment needs to be made since we removed the beginning of the
    # palette that didn't have any color
    return color + TRANSPARENT_END_EXCL

def map_item_to_nbt_file(frame, alpha_threshold, override_transparency=None):
    # Correct the list of map color ids (since it's not perfect)
    # ID 34 is snow or (255,255,255).
    # Since the palette only has 230ish colors and the rest are #FFFFFF,
    # indices greater than 207 must be set to 34, aka #FFFFFF
    yield create_map(
        matched_color_to_map_color(color, alpha, alpha_threshold,
                                   override_transparency)
        for color, alpha in zip(*frame)
    )

def image_to_nbt(image, palette_image, alpha_threshold=128, scale_dim=(1, 1),
                 quantize_method="median-cut", override_transparency=None):
    """Creates a generator that yields NBT map(s) from an image"""
    # Extract frame(s) from image
    # If it's a GIF, it will process more than one frame.
    # Otherwise, it'll just process the one.
    try:
        n_frames = image.n_frames
    except AttributeError:
        n_frames = 1
    # TODO: This tqdm call would be better if it measured map-wise instead of
    #       frame-wise for GIFs.
    for image_frame in tqdm(ImageSequence.Iterator(image), total=n_frames):
        for frame in partition_image_to_map_items(image_frame, palette_image,
                                                  scale_dim, quantize_method):
            yield from map_item_to_nbt_file(frame, alpha_threshold,
                                            override_transparency)

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        "fp", metavar="path", help="The file path of the image")
    parser.add_argument(
        "num", metavar="map-#", type=int,
        help="How many maps exist in your world.")
    parser.add_argument(
        "-d", "--dir", metavar="dir", default=".",
        help="The directory to save in. Defaults to working directory.")
    parser.add_argument(
        "-s", "--scale", metavar="W:H", default="1:1", type=str,
        help="How many item frames to be occupied in the horizontal and " +
        "vertical dimensions. Width or height may be omitted and it will " +
        "be scaled and centered accordingly")
    parser.add_argument(
        "-q", "--quiet", action="store_true", default=False,
        help="is used to remove the progress bar")
    parser.add_argument(
        "-a", "--alpha-threshold", metavar="N", default=128, type=int,
        help="The minimum alpha value for a pixel to be considered opaque. " +
        "Default is 128.")
    parser.add_argument(
        "-v", "--override", metavar="S", default="", type=str,
        help="will override transparent pixels with a color in hex format. " +
        "If left empty, transparent pixels will not be overrided.")
    parser.add_argument(
        "-m", "--quantize-method", metavar="S", default="median-cut", type=str,
        help="an optional quantize method, from the PIL docs")

    args = parser.parse_args()

    # Silence tqdm
    if args.quiet:
        tqdm = lambda it, *a, **k: it

    try:
        image = Image.open(args.fp)
        image.load()
    except FileNotFoundError as e:
        sys.exit(e)

    palette_image = load_palette()

    scale_dim = args.scale.split(":")
    if len(scale_dim) != 2:
        print("Error: incorrect scale given. " +
            "Should be one colon with at least one numeric value")
        sys.exit(1)

    if scale_dim[0] == "":
        scale_dim[0] = None
        scale_dim[1] = int(scale_dim[1])
    elif scale_dim[1] == "":
        scale_dim[0] = int(scale_dim[0])
        scale_dim[1] = None
    else:
        scale_dim = (int(scale_dim[0]), int(scale_dim[1]))

    if not (0 <= args.alpha_threshold <= 255):
        print("Error: alpha threshold should be from 0 to 255")
        sys.exit(1)

    if args.quantize_method not in ("median-cut", "max-coverage",
                                      "fast-octree", "libimagequant", "off"):
        print("Error: selected quantize method is unrecognized.")
        sys.exit(1)

    override_color = \
        match_color(hex_color_to_tuple(args.override), palette_image) \
        if args.override else \
        None

    try:
        for nbt_file in image_to_nbt(image, palette_image, args.alpha_threshold,
                                     scale_dim, args.quantize_method,
                                     override_transparency=override_color):
            nbt_file.write_file(os.path.join(args.dir, 'map_%d.dat' % args.num))
            args.num += 1
    
    except (FileNotFoundError, KeyboardInterrupt) as e:
        sys.exit(e)
    finally:
        image.close()
