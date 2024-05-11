import winreg
import re
import os
import subprocess
import tempfile
import shutil

def get_paths_from_file(filepath):
    # Read path values from specified file.
    paths_dict = {}
    try:
        with open(filepath, 'r') as file:
            for line in file:
                line = line.strip()
                program, location = line.split("=")
                paths_dict[program] = location
    except Exception:
        print(f"Warning: {filepath} is malformed or missing.")
    return paths_dict

def check_requirements_present(paths):
    # Check dependencies are accessible
    for program in ["ffmpeg", "bsab"]:
        try:
            program_path = program
            if paths.get(program):
                program_path = paths.get(program)
            # Run program by path, but do not care for output.
            subprocess.run(program_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            paths[program] = program_path
        except Exception:
            print(f"Missing dependency: {program}")
            return False
    return True

def find_skyrim_sounds_bsa_path(install_dir):
    try: 
        bethesda_dir = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Bethesda Softworks")
        idx = 0
        game_key_name = ""
        while (True):
            game_key_name = winreg.EnumKey(bethesda_dir, idx)
            if re.match("Skyrim", game_key_name):
                break
            idx += 1
        game_dir = winreg.OpenKey(bethesda_dir, game_key_name)
        return os.path.join(winreg.QueryValueEx(game_dir, "Installed Path")[0], r"Data\Skyrim - Sounds.bsa")
    except Exception:
        if install_dir:
            print("Unable to automatically determine Skyrim's install directory; using path defined in PATHS.txt")
            return os.path.join(install_dir, r"Data\Skyrim - Sounds.bsa")
        print("Unable to locate Skyrim's install directory; exiting")
        return

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
    # Step 0: Check all required dependencies and values are present
    paths = get_paths_from_file("PATHS.txt")
    if (not check_requirements_present(paths)):
        return
    for var in ["output_extension", "output_dir", "translation_map"]:
        if not paths[var]:
            print(f"{var} unspecified; exiting")
            return
    # Step 1: Find 'Skyrim - Sounds.bsa'.
    bsaPath = find_skyrim_sounds_bsa_path(paths["install_dir"])
    if not bsaPath:
        return
    # Step 2: Unpack said .bsa to a temporary folder.
    # Step 3: Locate only the relevant music files; exclusion list in exclusionOpts:
    temp_dir = tempfile.mkdtemp()
    exclusionOpts = '\
--exclude "sound\*" \
--exclude "music\\combat\\*finale.xwm" \
--exclude "music\\dlc01\\explore\\soulcairn\\palette\*" \
--exclude "music\\dread\\*" \
--exclude "music\\explore\\*\palette\*" \
--exclude "music\\reveal\\*" \
--exclude "music\\reward\\*" \
--exclude "music\\special\\mus_special*" \
--exclude "music\\special\\failure\\*" \
--exclude "music\\stinger\\*" \
--exclude "music\\mus_levelup_*" \
--exclude "music\\mus_discover_genericlocation*"'
    subprocess.run(f"{paths.get('bsab')} {exclusionOpts} -e \"{bsaPath}\" \"{temp_dir}\"")
    # Step 4: Call FFmpeg on each remaining file; convert to selected filetype.
    # Step 5: Rename each piece to its real name.
    translation_map = read_translation_map(paths.get("translation_map"))

    name_counter = 0
    total = len(translation_map.keys())
    for folder_path, _, file_names in os.walk(temp_dir):
        for filename in file_names:
            relative_path = os.path.relpath(os.path.join(folder_path, filename), start=temp_dir)
            if translation_map.get(relative_path):
                # FFmpeg command reasoning:
                # -n -> If file already exists, do not overwrite it.
                # Without this option, the script will prompt about name collisions, which are fine to ignore.
                # "From Past to Present" caused this issue during development.
                # -hide_banner -> As FFmpeg is invoked for every file, this would cause a significant amount of spam.
                # -loglevel fatal -> XWM seems to have issues with timings within each file; these can safely be ignored without warning the user.
                # -nostats -> Presenting stats for how long each individual file will take to convert is unhelpful.
                # -i -> File being inputted, relative to working directory {temp_dir}
                return_code = subprocess.run(f"{paths['ffmpeg']} -n -hide_banner -loglevel fatal -nostats -i \"{os.path.join(temp_dir, relative_path)}\" \"{os.path.join(paths['output_dir'], translation_map[relative_path])}.{paths['output_extension']}\"", cwd=temp_dir).returncode
                name_counter += 1
                if return_code == 0:
                    print(f"Wrote {os.path.join(paths['output_dir'], translation_map[relative_path])}.{paths['output_extension']} ({name_counter}/{total})")
    shutil.rmtree(temp_dir)
    # Step 6: Enjoy :)

if __name__ == "__main__":
    # Can use return to exit the program early.
    main()