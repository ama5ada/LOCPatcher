import tkinter as tk
from tkinter import ttk as ttk
import math
import urllib.request
import os
import zlib
import subprocess
import sys
import ssl
from datetime import datetime

unverified_context = ssl._create_unverified_context()

global updated_file_map
global outdated_file_list
global working_dir
global remote_patch_list
global remote_host
global default_patch_cache_list
global button_state_map
global button_cursor_map

default_patch_cache_list = ['Mist/Binaries/Win64/dsound.dll', 'Mist/Binaries/Win64/dsound.exp', 'Mist/Binaries/Win64/dsound.lib', 'Mist/Binaries/Win64/dsound.pdb', 'Mist/Binaries/Win64/steam_appid.txt', 'Mist/Binaries/Win64/Symbols.bin', 'Mist/Binaries/Win64/Plugins/ExamplePlugin.dll', 'Mist/Binaries/Win64/Plugins/ExamplePlugin.pdb', 'Mist/Content/Movies/.gitignore', 'Mist/Content/Movies/menu.mp4', 'Mist/Content/Paks/pakchunk9017-WindowsClient_P.pak', 'Mist/Content/Paks/pakchunk9017-WindowsClient_P.sig', 'Mist/Content/Paks/pmod/pmod_Ammo.pak', 'Mist/Content/Paks/pmod/pmod_Ammo.sig', 'Mist/Content/Paks/pmod/pmod_AmmoChest.pak', 'Mist/Content/Paks/pmod/pmod_AmmoChest.sig', 'Mist/Content/Paks/pmod/pmod_AncientCity.pak', 'Mist/Content/Paks/pmod/pmod_AncientCity.sig', 'Mist/Content/Paks/pmod/pmod_Asteroid.pak', 'Mist/Content/Paks/pmod/pmod_Asteroid.sig', 'Mist/Content/Paks/pmod/pmod_BoomBoxSounds.pak', 'Mist/Content/Paks/pmod/pmod_BoomBoxSounds.sig', 'Mist/Content/Paks/pmod/pmod_BoomBoxSounds2.pak', 'Mist/Content/Paks/pmod/pmod_BoomBoxSounds2.sig', 'Mist/Content/Paks/pmod/pmod_BoomBoxSounds3.pak', 'Mist/Content/Paks/pmod/pmod_BoomBoxSounds3.sig', 'Mist/Content/Paks/pmod/pmod_BoomBoxSounds4.pak', 'Mist/Content/Paks/pmod/pmod_BoomBoxSounds4.sig', 'Mist/Content/Paks/pmod/pmod_BoomBoxSounds5.pak', 'Mist/Content/Paks/pmod/pmod_BoomBoxSounds5.sig', 'Mist/Content/Paks/pmod/pmod_CanyonMap.pak', 'Mist/Content/Paks/pmod/pmod_CanyonMap.sig', 'Mist/Content/Paks/pmod/pmod_ClanEmblems.pak', 'Mist/Content/Paks/pmod/pmod_ClanEmblems.sig', 'Mist/Content/Paks/pmod/pmod_Configs.pak', 'Mist/Content/Paks/pmod/pmod_Configs.sig', 'Mist/Content/Paks/pmod/pmod_Cosmetics.pak', 'Mist/Content/Paks/pmod/pmod_Cosmetics.sig', 'Mist/Content/Paks/pmod/pmod_CraterMap.pak', 'Mist/Content/Paks/pmod/pmod_CraterMap.sig', 'Mist/Content/Paks/pmod/pmod_Equipments.pak', 'Mist/Content/Paks/pmod/pmod_Equipments.sig', 'Mist/Content/Paks/pmod/pmod_Exosuit.pak', 'Mist/Content/Paks/pmod/pmod_Exosuit.sig', 'Mist/Content/Paks/pmod/pmod_Explosions.pak', 'Mist/Content/Paks/pmod/pmod_Explosions.sig', 'Mist/Content/Paks/pmod/pmod_Flotilla.pak', 'Mist/Content/Paks/pmod/pmod_Flotilla.sig', 'Mist/Content/Paks/pmod/pmod_Foliage.pak', 'Mist/Content/Paks/pmod/pmod_Foliage.sig', 'Mist/Content/Paks/pmod/pmod_KaliVolcano.pak', 'Mist/Content/Paks/pmod/pmod_KaliVolcano.sig', 'Mist/Content/Paks/pmod/pmod_MechanicGirl1.pak', 'Mist/Content/Paks/pmod/pmod_MechanicGirl1.sig', 'Mist/Content/Paks/pmod/pmod_MechanicGirl2.pak', 'Mist/Content/Paks/pmod/pmod_MechanicGirl2.sig', 'Mist/Content/Paks/pmod/pmod_MechanicGirl3.pak', 'Mist/Content/Paks/pmod/pmod_MechanicGirl3.sig', 'Mist/Content/Paks/pmod/pmod_MechanicGirl4.pak', 'Mist/Content/Paks/pmod/pmod_MechanicGirl4.sig', 'Mist/Content/Paks/pmod/pmod_MechanicGirl5.pak', 'Mist/Content/Paks/pmod/pmod_MechanicGirl5.sig', 'Mist/Content/Paks/pmod/pmod_MechanicGirl6.pak', 'Mist/Content/Paks/pmod/pmod_MechanicGirl6.sig', 'Mist/Content/Paks/pmod/pmod_Mobs.pak', 'Mist/Content/Paks/pmod/pmod_Mobs.sig', 'Mist/Content/Paks/pmod/pmod_Mods.pak', 'Mist/Content/Paks/pmod/pmod_Mods.sig', 'Mist/Content/Paks/pmod/pmod_PoachingHut.pak', 'Mist/Content/Paks/pmod/pmod_PoachingHut.sig', 'Mist/Content/Paks/pmod/pmod_Pyramid.pak', 'Mist/Content/Paks/pmod/pmod_Pyramid.sig', 'Mist/Content/Paks/pmod/pmod_QoL.pak', 'Mist/Content/Paks/pmod/pmod_QoL.sig', 'Mist/Content/Paks/pmod/pmod_SleepingGiants.pak', 'Mist/Content/Paks/pmod/pmod_SleepingGiants.sig', 'Mist/Content/Paks/pmod/pmod_StringTables.pak', 'Mist/Content/Paks/pmod/pmod_StringTables.sig', 'Mist/Content/Paks/pmod/pmod_TestMap.pak', 'Mist/Content/Paks/pmod/pmod_TestMap.sig', 'Mist/Content/Paks/pmod/pmod_Traders.pak', 'Mist/Content/Paks/pmod/pmod_Traders.sig', 'Mist/Content/Paks/pmod/pmod_TradeStation.pak', 'Mist/Content/Paks/pmod/pmod_TradeStation.sig', 'Mist/Content/Paks/pmod/pmod_UI.pak', 'Mist/Content/Paks/pmod/pmod_UI.sig', 'Mist/Content/Paks/pmod/pmod_Walkers.pak', 'Mist/Content/Paks/pmod/pmod_Walkers.sig', 'Mist/Content/Paks/pmod/pmod_WalkersMesh_Battleship.pak', 'Mist/Content/Paks/pmod/pmod_WalkersMesh_Battleship.sig', 'Mist/Content/Paks/pmod/pmod_WalkersMesh_Domus.pak', 'Mist/Content/Paks/pmod/pmod_WalkersMesh_Domus.sig', 'Mist/Content/Paks/pmod/pmod_WalkersMesh_Falco.pak', 'Mist/Content/Paks/pmod/pmod_WalkersMesh_Falco.sig', 'Mist/Content/Paks/pmod/pmod_WalkerWeapons.pak', 'Mist/Content/Paks/pmod/pmod_WalkerWeapons.sig', 'Mist/Content/Paks/pmod/pmod_WarOkkam.pak', 'Mist/Content/Paks/pmod/pmod_WarOkkam.sig', 'Mist/Content/Paks/pmod/pmod_Worm.pak', 'Mist/Content/Paks/pmod/pmod_Worm.sig']

updated_file_map = {}
button_state_map = {}
button_cursor_map = {}
outdated_file_list = []
remote_patch_list = "http://loc.iambvc.it/client/patchlist.txt"
remote_host = "http://loc.iambvc.it/client/"

working_dir = os.getcwd() + "/"

# working_dir = "E:/SteamLibrary/steamapps/common/Last Oasis/"


"""
    Functions related to getting the patch list and identifying files that need to be downloaded or updated
"""


def check_patch_list():
    global updated_file_map
    global remote_patch_list
    add_status_text_line("Get patch list from " + remote_patch_list)
    update_label(action_label, "Get Patch List - Step 1/3")
    update_label(step_label, "Get Patch List from Server")
    with urllib.request.urlopen(remote_patch_list, context=unverified_context) as patchlist:
        content = patchlist.read().decode('utf-8')
    for file_info in content.split("\n"):
        if file_info != "":
            file_info_array = file_info.split(" ")
            updated_file_map[file_info_array[0]] = {'hash': file_info_array[1], 'size': file_info_array[2]}
    update_progress_bar(action_bar, 1)
    highlight_status_text("1", "green")


def check_local_files():
    global working_dir
    global updated_file_map
    global outdated_file_list
    validate_array = []
    outdated_file_list = []

    add_status_text_line("Check if local files exist")
    update_label(action_label, "Get Patch List - Step 2/3")
    update_label(step_label, "Check if local files exist - 0 /" + str(len(updated_file_map)))
    define_progress_bar(step_bar, "determinate", len(updated_file_map))

    # Build an array of file names that exist locally that need to be verified as up to date
    checked = 0
    for key in updated_file_map:
        add_log_text_line("Checking if file exists " + working_dir + key)
        if os.path.isfile(working_dir + key):
            validate_array.append(key)
        else:
            # If the file doesn't event exist locally mark it as outdated, so it will be downloaded
            add_log_text_line("File " + key + " does not exist locally")
            outdated_file_list.append(key)
        checked += 1
        update_label(step_label, "Check if local files exist - " + str(checked) + " / " + str(len(updated_file_map)))
        update_progress_bar(step_bar, checked)

    highlight_status_text("2", "green")
    update_progress_bar(action_bar, 2)

    create_change_list(validate_array)


def create_change_list(validate_array):
    global updated_file_map
    global outdated_file_list
    add_status_text_line("Validate local files")
    update_label(action_label, "Get Patch List - Step 3/3")
    update_label(step_label, "Check if local files are up to date - 0 /" + str(len(updated_file_map)))
    define_progress_bar(step_bar, "determinate", len(validate_array))
    checked = 0
    for file in validate_array:
        add_log_text_line("Validating File : " + working_dir + file)
        if not validate_file(file):
            outdated_file_list.append(file)

        checked += 1
        update_label(step_label, "Check if local files are up to date - " + str(checked) + " / " + str(len(validate_array)))
        update_progress_bar(step_bar, checked)

    highlight_status_text("3", "green")

    if len(outdated_file_list) > 0:
        add_status_text_line("RESULT : UPDATED REQUIRED")
        add_status_text_line("Found " + str(len(outdated_file_list)) + " old or missing files : ")
        highlight_status_text("4", "orange")
        highlight_status_text("5", "orange")
        for old_file in outdated_file_list:
            add_status_text_line(old_file)
    else:
        add_status_text_line("RESULT : UP TO DATE")
        add_status_text_line("Found " + str(len(outdated_file_list)) + " old or missing files")
        highlight_status_text("4", "green")
        highlight_status_text("5", "green")

    update_progress_bar(action_bar, 3)


def validate_file(file):
    global updated_file_map
    global working_dir
    local_file_size = os.stat(working_dir + file).st_size
    updated_file_size = int(updated_file_map[file]['size'])

    if local_file_size == updated_file_size:
        add_log_text_line("Local file size : " + convert_file_size(local_file_size) + " matches remote file size : " +
                          convert_file_size(updated_file_size))
        crc = 0
        remote_crc = updated_file_map[file]['hash'].upper()
        with open(working_dir + file, 'rb', 65536) as ins:
            for x in range(int((os.stat(working_dir + file).st_size / 65536)) + 1):
                crc = zlib.crc32(ins.read(65536), crc)
        crc = ('%08X' % (crc & 0xffffffff))
        if crc == remote_crc:
            add_log_text_line("Local file CRC : " + str(crc) + " matches remote file CRC : " +
                              str(remote_crc))
            return True
        else:
            add_log_text_line("File hashes do not match, adding file : " + file + " to list of outdated files")
    else:
        add_log_text_line("File sizes do not match, adding file : " + file + " to list of outdated files")
    return False


def determine_patch_result():
    global outdated_file_list
    if len(outdated_file_list) < 1:
        # If a patch is not necessary allow the game to be launched
        update_button(start_loc_client, "normal")
    else:
        # Enable the patch button
        update_button(patch_loc_mods, "normal")


"""
    Functions related to downloading or replacing the files identified as out of date
"""


def download_new_files():
    global updated_file_map
    global outdated_file_list
    global working_dir
    file_tries = {}
    add_log_text_line("Downloading new file versions from server")
    file_count = 0
    total_downloaded = 0
    total_to_download = 0
    for file in outdated_file_list:
        total_to_download += int(updated_file_map[file]['size'])
    update_label(action_label,
        "Get Updated Mod Paks - " + str(file_count) + " / " + str(len(outdated_file_list)) + "\n" +
        convert_file_size(total_downloaded) + " / " + convert_file_size(total_to_download) + "\n" +
        "{0:.0%}".format(total_downloaded/total_to_download))
    define_progress_bar(action_bar, "determinate", total_to_download)
    for file in outdated_file_list:
        file_name = file.split("/")[-1]
        check_dir(working_dir + file)
        add_status_text_line("Downloading : " + file_name + " to : " + working_dir + file_name)
        file_count += 1
        file_tries[file] = 0
        while True:
            download_size = get_new_file(file)
            add_log_text_line("Validating File : " + working_dir + file_name)
            if validate_file(file):
                total_downloaded += download_size
                highlight_status_text(str(outdated_file_list.index(file) + 1), "green")
                break
            else:
                add_log_text_line("FILE FAILED VALIDATION AFTER DOWNLOAD, RETRYING")
                file_tries[file] += 1
                highlight_status_text(str(outdated_file_list.index(file) + 1), "orange")
                if file_tries[file] > 2:
                    add_log_text_line("FILE FAILED TO DOWNLOAD AFTER " + str(file_tries[file]) + " ATTEMPTS, ABORTING RETRY.")
                    highlight_status_text(str(outdated_file_list.index(file) + 1), "red")
                    break
        update_progress_bar(action_bar, total_downloaded)
        update_label(action_label,
            "Get Updated Mod Paks - " + str(file_count) + " / " + str(len(outdated_file_list)) + "\n" +
            convert_file_size(total_downloaded) + " / " + convert_file_size(total_to_download) + "\n" +
            "{0:.0%}".format(total_downloaded/total_to_download))


def check_dir(filepath):
    folderpath = "/".join(filepath.split("/")[:-1])
    if not os.path.isdir(folderpath):
        add_log_text_line("Folder does not exist, creating folder: " + folderpath)
        os.makedirs(folderpath)


def get_new_file(file):
    global updated_file_map
    global remote_host
    global working_dir
    patch_file = urllib.request.urlopen(remote_host + file, context=unverified_context)
    if "../" in file:
        add_status_text_line("WARNING : directory traversal detected. Cancelling download. Tell Bryan if you see this.")
        return
    with open(working_dir + file, 'wb') as output:
        update_label(status_frame, "Downloading : " + file.split("/")[-1])
        define_progress_bar(step_bar, "determinate", int(updated_file_map[file]['size']))
        while True:
            downloaded_bytes = os.path.getsize(working_dir + file)
            update_label(step_label,
                "Download " + file.split("/")[-1] + " \n " + convert_file_size(downloaded_bytes) + " / " +
                convert_file_size(int(updated_file_map[file]['size'])) + "\n" +
                "{0:.0%}".format(downloaded_bytes/int(updated_file_map[file]['size'])))
            update_progress_bar(step_bar, downloaded_bytes)
            data = patch_file.read(131072)
            if data:
                output.write(data)
            else:
                break
    total_bytes = os.path.getsize(working_dir + file)
    update_label(step_label,
        "Download " + file.split("/")[-1] + " \n " + convert_file_size(total_bytes) + " / " +
        convert_file_size(int(updated_file_map[file]['size'])) + "\n" +
        "{0:.0%}".format(total_bytes/int(updated_file_map[file]['size'])))
    update_progress_bar(step_bar, total_bytes)
    return os.path.getsize(working_dir + file)


def launch_last_oasis_classic():
    """
        Function to launch the Last Oasis client
    """
    global working_dir
    add_log_text_line("Launching the game client")
    os.chdir(working_dir + "Mist/Binaries/Win64/")
    subprocess.call("start MistClient-Win64-Shipping.exe -noeac", shell=True)


def clear_last_oasis_classic_mods():
    """
        Function to clear Last Oasis Classic mods from the client
    """
    global default_patch_cache_list
    global working_dir
    for delete_file in default_patch_cache_list:
        print(delete_file)
        if os.path.isfile(working_dir + delete_file):
            add_status_text_line("Deleting file : " + delete_file)
            os.remove(working_dir + delete_file)
            highlight_status_text(str(default_patch_cache_list.index(delete_file) + 1), "green")


def export_logs_to_file():
    """
        Function to export logs to text file, so they can be looked at, if someone really wants to do that
        Function to export logs to text file, so they can be looked at, if someone really wants to do that
    """
    global working_dir
    log_box_text = log_text.get("1.0", "end-1c")
    lines = len(log_box_text.split("\n"))
    # Make new helper method to update any bar
    define_progress_bar(log_export_bar, "determinate", lines)
    log_export_bar.pack(side="left", expand="True", fill="x")
    if len(log_box_text) > 0:
        log_file_name = "log_" + str(datetime.now()).replace(":","_") + ".txt"
        log_export_label['text'] = "Sending logs to file " + log_file_name
        log_export_label.update()
        check_dir(working_dir + "patcher_logs/" + log_file_name)
        with open(working_dir + "patcher_logs/" + log_file_name, "w") as log_file:
            written = 0
            for line in log_box_text.split("\n"):
                log_file.writelines(line + "\n")
                written += 1
                update_progress_bar(log_export_bar, written)


"""
    Command functions for all the GUI buttons.
    These are executed when a button is clicked.
    Each functions generally handles :
     - Updating the GUI
     - Calling other functions that carry out more complex logic
"""


def get_patch_list_click():
    disable_button_actions()
    update_button(start_loc_client, "disabled")
    update_label(status_frame, "Status : Getting Patch List")
    clear_status_text()
    update_label(action_label, "Get Patch List - Step 0/3")
    define_progress_bar(action_bar, "determinate", 3)

    check_patch_list()
    check_local_files()
    determine_patch_result()

    update_label(status_frame, "Status : Got Patch List")
    get_patch_list['fg'] = "green"
    update_button(log_export_button, "normal")
    enable_button_actions()


def patch_loc_mods_click():
    disable_button_actions()
    update_label(status_frame, "Status : Patching")
    clear_status_text()
    download_new_files()
    update_button(patch_loc_mods, "disabled")
    update_button(start_loc_client, "normal")
    update_label(status_frame, "Status : Patched")
    enable_button_actions()


def start_loc_client_click():
    disable_button_actions()
    update_label(status_frame, "Status : Starting Client")
    clear_status_text()
    add_status_text_line("Starting LOC client...")
    launch_last_oasis_classic()
    enable_button_actions()


def clear_loc_mods_click():
    disable_button_actions()
    update_label(status_frame, "Status : Clearing LOC Mods")
    clear_status_text()
    clear_last_oasis_classic_mods()
    update_button(log_export_button, "normal")
    enable_button_actions()


def export_logs_to_file_click():
    disable_button_actions()
    update_label(status_frame, "Status : Exporting logs to file")
    export_logs_to_file()
    enable_button_actions()


"""
    Helper functions for updating tkinter GUI elements
"""


def update_button(button, state):
    global button_state_map
    global button_cursor_map
    if state == "normal":
        button['state'] = "normal"
        button['cursor'] = "hand2"
        button_state_map[button] = state
        button_cursor_map[button] = "hand2"
    else:
        button['state'] = "disabled"
        button['cursor'] = "arrow"
        button_state_map[button] = state
        button_cursor_map[button] = "arrow"


def enable_button_actions():
    global button_state_map
    global button_cursor_map
    for button in button_state_map:
        button['state'] = button_state_map[button]
        button['cursor'] = button_cursor_map[button]


def disable_button_actions():
    global button_state_map
    for button in button_state_map:
        button['state'] = "disabled"
        button['cursor'] = "arrow"


def update_label(label, new_label_text):
    label['text'] = new_label_text
    label.update()


def add_status_text_line(text_line):
    status_text['state'] = "normal"
    status_text.insert(tk.END, text_line + "\n")
    status_text['state'] = "disabled"
    status_text.update()
    add_log_text_line(text_line)


def highlight_status_text(highlight_line, highlight_color):
    status_text.tag_add("line" + highlight_line, highlight_line + ".0", highlight_line + ".end")
    status_text.tag_config("line" + highlight_line, foreground=highlight_color)
    status_text.update()


def clear_status_text():
    status_text['state'] = "normal"
    status_text.delete("1.0", "end")
    status_text['state'] = "disabled"
    status_text.update()


def add_log_text_line(log_line):
    log_text['state'] = "normal"
    log_text.insert(tk.END, log_line + "\n")
    log_text['state'] = "disabled"
    log_text.update()


def define_progress_bar(bar, mode, maximum):
    bar['mode'] = mode
    bar['maximum'] = maximum
    bar.update()


def update_progress_bar(bar, progress):
    bar['value'] = progress
    bar.update()


def resource_path(relative_path):
    """
        Helper function to add the LO symbol to the shipped patcher
    """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def convert_file_size(size_in_bytes):
    """
        Helper function to convert file sizes to the largest logical denominator
    """
    if size_in_bytes == 0:
        return "0B"
    if not isinstance(size_in_bytes, int):
        return "NaN"
    size_list = ["B", "KB", "MB", "GB", "TB"]
    size_index = int(math.floor(math.log(size_in_bytes, 1024)))
    p = math.pow(1024, size_index)
    size = round(size_in_bytes / p, 2)
    return "%s %s" % (size, size_list[size_index])


if __name__ == '__main__':
    """
        Create the GUI in a tkinter window
    """
    window = tk.Tk()
    window.title("Last Oasis Classic Launcher")
    #logoPath = resource_path('MistServer_101.ico')
    #window.iconbitmap(logoPath)

    window.maxsize(900, 600)
    window.minsize(900, 600)

    bg_color = 'royalblue1'

    action_frame = tk.Frame(window, bg=bg_color, width=300, height=600)
    action_frame.pack(side="left", expand=False)
    action_frame.propagate(False)

    button_frame = tk.Frame(action_frame, bg=bg_color, width=300, height=200, bd=1)
    button_frame.pack(expand=True, fill='x')
    button_frame.propagate(False)

    get_patch_list = tk.Button(button_frame, text="Get Patch List", command=get_patch_list_click, state="normal",
                            pady=5, cursor="hand2")
    patch_loc_mods = tk.Button(button_frame, text="Patch LOC Mods", command=patch_loc_mods_click, state="disabled",
                            pady=5, cursor="arrow")
    start_loc_client = tk.Button(button_frame, text="Start LOC Client", command=start_loc_client_click,
                            state="disabled", pady=5, cursor="arrow")
    clear_loc_mods = tk.Button(button_frame, text="Clear LOC Mods", command=clear_loc_mods_click, state="normal",
                            pady=5, cursor="hand2")

    button_state_map[get_patch_list] = "normal"
    button_cursor_map[get_patch_list] = "hand2"

    button_state_map[patch_loc_mods] = "disabled"
    button_cursor_map[patch_loc_mods] = "arrow"

    button_state_map[start_loc_client] = "disabled"
    button_cursor_map[start_loc_client] = "arrow"

    button_state_map[clear_loc_mods] = "normal"
    button_cursor_map[clear_loc_mods] = "hand2"

    get_patch_list.pack(expand=True, fill='both', pady=5, padx=10)
    patch_loc_mods.pack(expand=True, fill='both', pady=5, padx=10)
    start_loc_client.pack(expand=True, fill='both', pady=5, padx=10)
    clear_loc_mods.pack(expand=True, fill='both', pady=5, padx=10)

    status_frame = tk.LabelFrame(action_frame, bg=bg_color, width=300, height=200, text="Status : Waiting")
    status_frame.pack(expand=False)
    status_frame.propagate(False)

    status_text = tk.Text(status_frame, state="disabled", cursor="arrow", wrap="word")
    status_text.pack(expand=False)

    progress_frame = tk.Frame(action_frame, bg=bg_color, width=300, height=200, pady=5)
    progress_frame.pack(expand=True)
    progress_frame.propagate(False)

    step_label = tk.Label(progress_frame, text="Waiting", bg=bg_color)
    step_bar = ttk.Progressbar(progress_frame, orient='horizontal', mode='determinate', length=280)
    action_label = tk.Label(progress_frame, text="Waiting", bg=bg_color)
    action_bar = ttk.Progressbar(progress_frame, orient='horizontal', mode='determinate', length=280)

    step_label.pack()
    step_bar.pack(padx=10, pady=5, expand=True, fill="x")
    action_label.pack()
    action_bar.pack(padx=10, pady=5, expand=True, fill="x")

    log_frame = tk.Frame(window, bg='black', width=600, height=600)
    log_frame.pack(side="left", expand=False)
    log_frame.propagate(False)

    log_label = tk.Label(log_frame, bg='black', fg='white', text="Logs")
    log_label.pack(side="top")

    log_text_frame = tk.Frame(log_frame, bg='black', width=590, height=500, padx=5, pady=5)
    log_text_frame.pack(expand=True)
    log_text_frame.propagate(False)

    log_text = tk.Text(log_text_frame, state="disabled", cursor="arrow", wrap="word", bg="black", bd=0, fg="white")
    log_text.pack(expand=True, fill="both")

    log_action_frame = tk.Frame(log_frame, width=590, height=50, padx=5, pady=5, bg="black")
    log_action_frame.pack(expand=True)
    log_action_frame.propagate(False)

    log_export_button = tk.Button(log_action_frame, text="Export Logs to File", command=export_logs_to_file_click,
                                  state = "disabled")
    log_export_button.pack(side="left")

    button_state_map[log_export_button] = "disabled"
    button_cursor_map[log_export_button] = "arrow"

    log_export_label = tk.Label(log_action_frame, text="", bg="black", fg="white")
    log_export_label.pack(side="left")

    log_export_bar = ttk.Progressbar(log_action_frame, length=100)

    window.mainloop()