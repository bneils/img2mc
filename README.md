# minecraft-map-maker
Converts images to Minecraft maps.

# Command-line interface
The program is CLI-friendly, simply invoke with `py mapped.py <file-path> <map-#>`.
<br>You are also allowed to specify the directory to save it in with the `--dir` option.

# How do I view it now that it's been generated?
Enter any Minecraft world you have file-access rights to, and create a map.
Hover over it in your inventory and it should say "#0" or any number. This is the number that should've been specified when you generated the map. Navigate to the `data/` directory within your world, and place `map_0.dat` within the folder.
<br>
If you want to reset all the maps, then delete any files in `data/` that start with `map_` and `idcounts.dat` (which holds the newest map id)
