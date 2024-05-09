# Skyrim OST Extractor:

You must have the following programs on your PATH, or made accessible otherwise. 
* [BSA Browser](https://www.nexusmods.com/skyrimspecialedition/mods/1756) (bsab.exe)
* [FFmpeg](https://ffmpeg.org/download.html) (ffmpeg.exe)

They can be made accessible by specifying the path - excluding quotation marks - to the executable in PATHS.txt (found next to the script)
The format taken in from PATHS.txt is as follows:  
`variable_name=X:\Path\To\Program.exe` or `variable_name=some data`


The variables that must be set are:
* translation_map -> Set a custom name translation. There is one shipped with the script.
* output_extension -> Set to any format ffmpeg accepts, without a prefixed '.'.
* output_dir -> Set to the directory you want the OST to be saved to.

These are **not** preconfigured, you will have to change them.

Some paths can be autodetected, but may need to be manually set.
Variables that may need to be set are:
* ffmpeg -> Path to the FFmpeg executable.
* bsab -> Path to the bsab executable.
* install_dir -> Path to your Skyrim install.

Note: This script is designed for Windows, and may not function correctly on other operating systems, even if compatibility tools are used.