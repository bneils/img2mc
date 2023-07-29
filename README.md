
# minecraft-map-maker
Converts images to custom Minecraft maps.

- [x] CLI-friendly with progressbar (tqdm)
- [x] Efficient color comparisons (PIL) with dithering quantization.
- [x] GIF support
- [x] Image scaling
- [x] Easy to update color palette for new versions of Minecraft (web scraping script)

# Command-line interface
## Optional
You may invoke `python3 dev-tools/generate_palette.py` to update the palette between versions of Minecraft.
This isn't that important since it will be invoked automatically when the script first runs.
Also, you don't have to worry about new versions of Minecraft breaking your maps, since the palette only adds new colors to the end.
## Generating a map
The command line options are provided with `-h`. However, this will explain what they do and what you should call it with.

You should call it like:

``` python3 mapped.py image.png 0 ```

The script will convert `image.png` into a map(s) starting at map ID #0.
The options are:
- `-h` or `--help` will print out descriptions of the options.
- `-d` or `--dir` will save the map(s) in the directory you specify.
- `-s` or `--scale` will scale the image across W:H maps.
- `-q` or `--quiet` will remove the progressbar, useful if you're using this in a script or GUI wrapper.
- `-a` or `--alpha-threshold` will define a threshold for what pixels should be considered transparent. This is best for images that have gradual alpha changes. If a semi-transparent pixel falls above the threshold, then its RGB values will take its place. You can use this to ignore transparency with `-a 0` or make everything transparent with `-a 255` (bwahaha).
- `-v` or `--override` will override transparent pixels with a color in hex format (e.g. FFFFFF). It will pick the closest approximation to that color.
- `-m` or `--quantize-method` will change the method of dithering. Its options are: "median-cut" (default), "max-coverage", "fast-octree", "libimagequant", and "off". These are derived from the [PIL documentation](https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.quantize). If you dislike or want to tweak the dithering, this parameter will be useful. Note that "libimagequant" may not be available on your system (or virtual environment).

The `--scale` flag should be supplied with a ratio (e.g. 3:3).
By default, it's 1:1. When the ratio has two integers, it will force the aspect ratio of the resulting image and fill the region.
However, if you leave out a dimension (e.g. 3: ), it will have to guess the resulting length or width so that the image keeps its aspect ratio.
The resulting image will be centered in whatever dimension you leave out.
The margins will be black transparent pixels, but will display as empty in the map.

If you want to convert a video to a GIF using ffmpeg, this is a handy trick:

```ffmpeg -i *.mp4 -vf "fps=20,scale=-1:128,crop=128:128" -loop 0 out.gif```

If you supply the script with a GIF, then it will process every frame regardless of FPS.

# How do I view it now that it's been generated?
Enter any Minecraft world you have file-access rights to, and create a number of maps.
If you have 3 map files and started at map #0, you want to generate or have generated maps #0 to #2.
Exit and save the world and override the map files in the `data` directory with the ones you generated.

If you want to reset all the maps, then delete any files in `data` that start with `map_` and `idcounts.dat` (which holds the newest map id)

# Example
![Andromeda viewed in a map](https://github.com/bneils/minecraft-map-maker/blob/main/andromeda_example.png)
