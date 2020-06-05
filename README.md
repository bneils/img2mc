# minecraft-map-maker
Converts images to custom Minecraft maps.

- [x] CLI-friendly with progressbar
- [x] Efficient color comparisons
- [x] Modular
- [x] GIF support
- [x] Partition support
- [x] Dithered

# Command-line interface
Simply invoke with `py mapped.py <file-path> <map-#>`.
<br>
Additional arguments include `--dir`, `--quiet`, `--alpha-threshold`, `--x-box-n`, and `--y-box-n`.

# How do I view it now that it's been generated?
Enter any Minecraft world you have file-access rights to, and create a map.
Hover over it in your inventory and it should say "#0", or any other number. This is the number that should've been specified when you generated the map. Navigate to the `data/` directory within your world, and place `map_0.dat` within the folder, replacing the map that was there before.
<br>
If you want to reset all the maps, then delete any files in `data/` that start with `map_` and `idcounts.dat` (which holds the newest map id)

# Example
![Andromeda viewed in a map](https://github.com/bneils/minecraft-map-maker/blob/master/andromeda_example.png)
