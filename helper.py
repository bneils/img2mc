from numpy import asarray
from PIL import Image
from math import ceil
from nbt.nbt import *

def resize_keep_ratio(image, value, setWidth=True):
    """Resize but keep the ratio"""
    return image.resize(
        (value, value * image.size[1] // image.size[0]) if setWidth else 
        (value * image.size[0] // image.size[1], value)
    )

def partitionAndMap(image, palimage, fitScale=0, box_dim=(1, 1)):
    """Returns a list of tuples containing linear map ids and alpha values"""

    # Check args
    if len(box_dim) != 2:
        raise ValueError("Not enough dimensions provided in box_dim")
    box_dim = [int(d) for d in box_dim]
    fitScale = int(fitScale)

    # We need opacity to determine transparency
    image = image.convert("RGBA")

    # Crop image if not using scaling
    if fitScale > 0:
        # Determine the grid space occupied by the image by using the shorter side as the fixed-length unit,
        # and the longer side as the one with padding
        image = resize_keep_ratio(image, value=fitScale * 128, setWidth=image.size[1] > image.size[0])

        # Measure how many cells this will take in either dimension
        box_dim = ceil(image.size[0] / 128), ceil(image.size[1] / 128)
        
        # Create a blank image, and paste the fixed-ratio scaled image to it, with padding to center it.
        newim = Image.new('RGBA', (box_dim[0] * 128, box_dim[1] * 128))
        paddingLeft = (newim.size[0] - image.size[0]) // 2
        paddingTop = (newim.size[1] - image.size[1]) // 2
        newim.paste(image, (paddingLeft, paddingTop))
        image = newim
    else:
        image = image.resize((box_dim[0] * 128, box_dim[1] * 128))

    # Put pixels into rows and columns for easy partitioning
    alphas = asarray(image.getdata(3)).reshape(image.size[::-1])
    mapIds = asarray(image.convert('RGB').quantize(palette=palimage, colors=palimage.size[1] // 3))

    # Now use NumPy's matrix slicing and then convert it to a linear array
    # The tuple represents the array of indices and alphas
    return [
        (mapIds[y:y + 128, x:x + 128].reshape(128*128), alphas[y:y + 128, x:x + 128].reshape(128*128))
        for y in range(0, image.height, 128)
        for x in range(0, image.width, 128)
    ]


def create_map(mapColorIds):
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
    return nbtfile
