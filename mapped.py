#!/usr/bin/env python3
__author__ = "Ben Neilsen"

from PIL import Image, ImageSequence
from argparse import ArgumentParser
from tqdm import tqdm
import csv
import os
import sys

from helper import *

# Initialize palette
with open('dev-tools/palette.csv') as f:
    channels = [int(col) for row in csv.reader(f, delimiter=',') for col in row]
    palimage = Image.new('P', (0, 0))
    palimage.putpalette(channels)
    numColors = len(channels) // 3

def frameToMap(frame, alpha_threshold):
    # Correct the list of map color ids (since it's not perfect)
    # ID 34 is snow or (255,255,255).
    # Since the palette only has 230ish colors (with the rest being (255,255,255), indices greater than 207 must be set to 34)
    yield create_map(
        [(i if 3*4 <= i < numColors else 34) if alpha >= alpha_threshold else 0 for i, alpha in zip(*frame)]
    )

def imagenbt(image, fitScale=0, alpha_threshold=128, box_n=(1, 1)):
    """Creates a generator that yields NBT map(s) from an image"""
    
    # Extract frame(s) from image
    if 'loop' in image.info: # This image must be a GIF
        for imageFrame in tqdm(ImageSequence.Iterator(image), total=image.n_frames):
            for frame in partitionAndMap(imageFrame, palimage, fitScale, box_n):
                yield from frameToMap(frame, alpha_threshold)
    else:
        for frame in partitionAndMap(image, palimage, fitScale, box_n):
            yield from frameToMap(frame, alpha_threshold)

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('fp', metavar='path', help='the file path of the image')
    parser.add_argument('num', metavar='map-#', type=int, help='how many maps exist in your world.')
    parser.add_argument('-d', '--dir', metavar='dir', default='.', help="the directory to save in. Defaults to working directory.")
    parser.add_argument('-x', '--x-box-n', metavar='X', default=1, type=int, help="how many horizontal maps to split the image into.")
    parser.add_argument('-y', '--y-box-n', metavar='Y', default=1, type=int, help="how many vertical maps to split the image into.")
    parser.add_argument('-q', '--quiet', action='store_true', default=False, help="is used to remove the progress bar")
    parser.add_argument('-a', '--alpha-threshold', metavar='N', default=128, type=int, help="the minimum alpha value for a value to be considered opaque. Default is 128.")
    parser.add_argument('-f', '--fit', metavar='S', default=0, type=int, help="find best fit, takes scale, does nothing if not positive")

    args = parser.parse_args()

    # Silence tqdm
    if args.quiet:
        tqdm = lambda it, *a, **k: it

    try:
        image = Image.open(args.fp)
        image.load()
    except FileNotFoundError as e:
        sys.exit(e)

    try:
        for nbtfile in imagenbt(image, args.fit, args.alpha_threshold, (args.x_box_n, args.y_box_n)):
            nbtfile.write_file(os.path.join(args.dir, 'map_%d.dat' % args.num))
            args.num += 1
    
    except (FileNotFoundError, KeyboardInterrupt) as e:
        sys.exit(e)
    finally:
        image.close()
