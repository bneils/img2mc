from numpy import asarray
from PIL import Image
from math import ceil

def resize_image_dim(image, width=None, height=None):
    """Resize an image according to one dimension"""
    if width != None and height != None:
        raise ValueError("Can only set one dimension")
    if width != None:
        return image.resize((width, width * image.size[1] // image.size[0]))
    if height != None:
        return image.resize((height * image.size[0] // image.size[1], height))
    return image


def partition_image(image, fitScale=0, box_dim=(2, 2)):
    """Takes in a (x, y) box count, which both default to 2"""
    
    x_width, y_width = box_dim
    
    # Convert to a size that would fit in (x_width,y_width) maps
    image = image.convert("RGBA")

    # Crop image if not using scaling
    if fitScale > 0:
        # Resize image to fit box
        if image.size[0] > image.size[1]:
            y_width = fitScale
            x_width = ceil(image.size[0] / image.size[1] * fitScale)
            image = resize_image_dim(image, height=fitScale * 128)
        elif image.size[1] > image.size[0]:
            x_width = fitScale
            y_width = ceil(image.size[1] / image.size[0] * fitScale)
            image = resize_image_dim(image, width=fitScale * 128)
        
        newim = Image.new('RGBA', (x_width * 128, y_width * 128))
        paddingLeft = (newim.size[0] - image.size[0]) // 2
        paddingTop = (newim.size[1] - image.size[1]) // 2
        box_dim = (x_width, y_width)
        newim.paste(image, (paddingLeft, paddingTop))
        image = newim
    else:
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