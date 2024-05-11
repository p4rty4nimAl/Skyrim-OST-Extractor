import winreg
import regex
import os
import subprocess
import tempfile
import shutil

def get_paths_from_file(filepath):
    try:
        file = open(filepath, 'r')
        pathsDict = {}
        nextLine = file.readline().strip()
        while (nextLine):
            program, location =  nextLine.split("=")
            pathsDict[program] = location
            nextLine = file.readline().strip()
        return pathsDict
    except Exception:
        print("Warning: PATHS.txt is malformed or missing.")
        return {}

def check_requirements_present(paths):
    for program in ["ffmpeg", "bsab"]:
        try:
            if (paths[program] and paths[program] != ""):
                subprocess.run(paths[program], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(program, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                paths[program] = program
        except Exception:
            print(f"Missing dependency: {program}")
            return False
    return True

def find_skyrim_sounds_bsa_path(install_dir):
    try: 
        bethesdaDir = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Bethesda Softworks")
        i = 0
        gameKeyName = ""
        while (True): 
            gameKeyName = winreg.EnumKey(bethesdaDir, i)
            if regex.match("Skyrim", gameKeyName):
                break
            i += 1
        gameDir = winreg.OpenKey(bethesdaDir, gameKeyName)
        return os.path.join(winreg.QueryValueEx(gameDir, "Installed Path")[0], r"Data\Skyrim - Sounds.bsa")
    except Exception:
        if (install_dir != ""):
            print("Unable to automatically determine Skyrim's install directory; using path defined in PATHS.txt")
            return os.path.join(install_dir, r"Data\Skyrim - Sounds.bsa")
        print("Unable to locate Skyrim's install directory; exiting")
        raise Exception(-1)

def read_translation_map(filepath):
    if not filepath or filepath == "":
        filepath = "translation_map_en.csv"
    translation_map = {}
    try:
        file = open(filepath, 'r')
        nextLine = file.readline().strip()
        while (nextLine):
            dev_name, friendly_name =  nextLine.split(":")
            translation_map[dev_name] = friendly_name
            nextLine = file.readline().strip()
    except Exception:
        print("Unable to read translation map provided.")
    return translation_map

def main():
    paths = get_paths_from_file("PATHS.txt")
    if (not check_requirements_present(paths)):
        return
        return
    for var in ["output_extension", "output_dir", "translation_map"]:
        if not paths[var]:
            print(f"{var} unspecified; exiting")
    # Step 1: Find 'Skyrim - Sounds.bsa'.
    bsaPath = find_skyrim_sounds_bsa_path(paths["install_dir"])
    print(bsaPath)
    # Step 2: Unpack said .bsa to a temporary folder.
    # Step 3: Locate only the relevant music files; exclusion list in exclusionOpts:
    temp_dir = tempfile.mkdtemp()
    exclusionOpts = r"""--exclude "sound\*" --exclude "music\combat\*finale.xwm" --exclude "music\dlc01\explore\soulcairn\palette\*" --exclude "music\dread\*" --exclude "music\explore\*\palette\*" --exclude "music\reveal\*" --exclude "music\reward\*" --exclude "music\special\mus_special*" --exclude "music\special\failure\*" --exclude "music\stinger\*" --exclude "music\mus_levelup_*" --exclude "music\mus_discover_genericlocation*" """
    subprocess.run(f"{paths['bsab']} {exclusionOpts} -e \"{bsaPath}\" \"{temp_dir}\"")
    
    # Step 4: Call FFmpeg on each remaining file; convert to selected filetype.
    # Step 5: Rename each piece to its real name.
    translation_map = read_translation_map(paths["translation_map"])
    i = 0
    total = len(translation_map.keys())
    for folder_path, _, file_names in os.walk(temp_dir):
        for filename in file_names:
            relative_path = os.path.relpath(os.path.join(folder_path, filename), start=temp_dir)
            if translation_map[relative_path]:
                # -n -> skip instead of overwriting
                # -hide_banner -> makes it quieter
                # -loglevel fatal -> do not warn about xwm timings being silly
                # -nostats -> do not care how long it is going to take
                # -i -> input file
                return_code = subprocess.run(f"{paths['ffmpeg']} -n -hide_banner -loglevel fatal -nostats -i \"{os.path.join(temp_dir, relative_path)}\" \"{os.path.join(paths['output_dir'], translation_map[relative_path])}.{paths['output_extension']}\"", cwd=temp_dir).returncode
                i += 1
                if (return_code == 0):
                    print(f"Wrote {os.path.join(paths['output_dir'], translation_map[relative_path])}.{paths['output_extension']} ({i}/{total})")
    shutil.rmtree(temp_dir)
    # Step 6: Enjoy :)

if __name__ == "__main__":
    # Can use return to exit the program early.
    main()