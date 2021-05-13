#!/usr/bin/env python3
__author__ = "Ben Neilsen"

from PIL import Image
from nbt.nbt import *
from numpy import asarray
from argparse import ArgumentParser
import csv
from tqdm import tqdm
import os, sys

# Initialize palette
with open('dev-tools/palette.csv') as f:
    palimage = Image.new('P', (1, 208*3))
    channels = [int(col) for row in csv.reader(f, delimiter=',') for col in row]
    palimage.putpalette(channels)


def crop(image):
    w, h = image.size
    if w > h:
        left = (w - h) // 2
        return image.crop((left, 0, left + h, h))
    elif h > w:
        top = (h - w) // 2
        return image.crop((0, top, w, top + w))
    else:
        return image
        
    
def partition_image(image, useScaling=True, box_dim=(2, 2)):
    """Takes in a (x, y) box count, which both default to 2"""
    
    x_width, y_width = box_dim
    
    # Convert to a size that would fit in (x_width,y_width) maps
    image = image.convert("RGBA")
    if not useScaling:
        image = crop(image)
    image = image.resize((x_width * 128, y_width * 128))
    
    if box_dim == (1, 1):
        return [image]

    # Put pixels into rows
    pixels = asarray(image)
    
    return [
        Image.fromarray(pixels[y:y + 128, x:x + 128]) 
        for y in range(0, image.height, 128)
        for x in range(0, image.width, 128)
    ]
    

def imagenbt(image, useScaling=True, alpha_threshold=128, box_n=(1, 1)):
    """Creates a generator that yields NBT map(s) from an image"""
    
    # Extract frame(s) from image
    if 'loop' in image.info: # This image must be a GIF
        frames = []
        for i in range(image.n_frames):
            image.seek(i)
            frames += partition_image(image.copy(), useScaling, box_n)
    else:
        frames = partition_image(image, useScaling, box_n)

    # Loop through frame(s)
    for frame in tqdm(frames):
        alpha_channel = frame.getdata(3)
        
        # Collect a list of map color ids by finding the closest color's indice 
        mapColorIds = frame.convert('RGB').quantize(palette=palimage, colors=208)

        # Correct the list of map color ids (since it's not perfect)
        # ID 34 is snow or (255,255,255).
        # Since the palette only has 208 colors (with the rest being (255,255,255), indices greater than 207 must be set to 34)
        mapColorIds = [(index if index < 208 else 34) if alpha >= alpha_threshold else 0 for index, alpha in zip(mapColorIds.getdata(), alpha_channel)]
        
        # Begin constructing the NBT file described at https://minecraft.gamepedia.com/Map_item_format#map_.3C.23.3E.dat_format
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
            TAG_Short(name = "width", value = 128),
        ])

        # Load image data
        imageData = TAG_Byte_Array(name = "colors")
        imageData.value = mapColorIds
        data.tags.append(imageData)

        frame.close()
        yield nbtfile


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('fp', metavar='path', help='the file path of the image')
    parser.add_argument('num', metavar='map-#', type=int, help='how many maps exist in your world.')
    parser.add_argument('-d', '--dir', metavar='dir', default='.', help="the directory to save in. Defaults to working directory.")
    parser.add_argument('-x', '--x-box-n', metavar='X', default=1, type=int, help="how many horizontal maps to split the image into.")
    parser.add_argument('-y', '--y-box-n', metavar='Y', default=1, type=int, help="how many vertical maps to split the image into.")
    parser.add_argument('-q', '--quiet', action='store_true', default=False, help="is used to remove the progress bar")
    parser.add_argument('-a', '--alpha-threshold', metavar='N', default=128, type=int, help="the minimum alpha value for a value to be considered opaque. Default is 128.")
    parser.add_argument('-c', '--crop', action='store_true', default=False, help="crop instead of scaling")

    args = parser.parse_args()

    # Silence tqdm
    if args.quiet:
        tqdm = lambda it, *a, **k: it

    try:
        image = Image.open(args.fp)
    except FileNotFoundError as e:
        sys.exit(e)

    try:
        for nbtfile in imagenbt(image, not args.crop, args.alpha_threshold, (args.x_box_n, args.y_box_n)):
            nbtfile.write_file(os.path.join(args.dir, 'map_%d.dat' % args.num))
            args.num += 1
    
    except (FileNotFoundError, KeyboardInterrupt) as e:
        image.close()
        sys.exit(e)
        
    image.close()
