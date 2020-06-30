import csv
import winsound
import PySimpleGUI as sg
import os
import time


# PARTS FEEDER SYSTEM
#
# VIOS FILE (xxx.txt) -> extracted job data (extracted_job_data) -> sync'd job data (sync_job_data)
# Feeders data - separate csv with all physical feeder info


# Returns a 2D array of raw feeder data: [i, j]
# i is index
# j is un-formatted lines of the parts feeder info
def extract_raw_vios_feeder_data(file_loc):
    fd_data = 0
    res = []
    res_internal = []
    first_line = 1
    i = 0
    for line in file_loc:
        if fd_data:  # We are in FD section
            if ("&F " in line) or ("End_of_FD" in line):
                if not first_line:
                    res.append(res_internal)
                    res_internal = []
                    i = 0
                else:
                    first_line = 0
            res_internal.append(line)
            i = i + i

        if "End_of_BD" in line:
            fd_data = 1
        if "End_of_FD" in line:
            return res


# Returns a 2D array of formatted feeder data [i, j]
# i is index
# j is [Manf. part no, feeder type, feeder width]
def format_raw_feeder_data(file_loc):
    raw = extract_raw_vios_feeder_data(file_loc)
    res = []
    for i in raw:
        feeder_size = int(i[3][2:4].strip())
        switch = {
            0: 8,
            1: 8,
            2: 12,
            3: 12,
            4: 16,
            5: 24,
            6: 32,
            7: 32,
            8: 44,
            9: 56
        }
        res_internal = [i[1].split('    ', 1)[0].strip(), str(switch.get(feeder_size))]
        f_slot = int(i[5].split('     ')[2].strip())
        if f_slot < 64:
            f_slot += 1
        if f_slot > 64:
            f_slot += 37

        res_internal.append(str(f_slot))
        res.append(res_internal)
    return res


# Writes formatted feeder data to output.csv
# MANF PART NO, TAPE WIDTH, FEEDER SLOT
def write_extracted_job_data(file_loc, output_folder):
    with open(output_folder + '\extracted_job_data.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["MANF PART NO", "TAPE WIDTH", "FEEDER SLOT"])
        val = format_raw_feeder_data(file_loc)
        for i in val:
            writer.writerow(i)


# opens vios file and returns the file stream
def open_vios_file(file_loc):
    with open(file_loc) as file:  # Use file to refer to the file object
        return file.readlines()


# Returns true if vios_file is valid VIOS data
def valid_vios_file(vios_file):
    return "&I.COMMENT=Philips_EMT_bv" in vios_file[2]


# Returns sync'd job data
# MANF PART NO, FEEDER WIDTH, FEEDER ID	SLOT
def gen_syncd_job_data(feeder_loc, formatted_data_loc):
    matched_job_data = []  # [manf part no, feeder width, feeder ID, slot]

    with open(feeder_loc, newline='') as file1:
        feeder_info = csv.DictReader(file1, delimiter=',')  # [FEEDER SIZE, FEEDER ID]
        feeder_info = list(feeder_info)

    with open(formatted_data_loc, newline='') as file2:
        curr_job_data = csv.DictReader(file2, delimiter=',')  # [MANF PART NO, TAPE WIDTH, FEEDER SLOT]
        curr_job_data = list(curr_job_data)

    used_feeder_ids = []
    for i in range(0, len(curr_job_data)):
        row = []
        for j in range(0, len(feeder_info)):
            if (curr_job_data[i]["TAPE WIDTH"] == feeder_info[j]["FEEDER SIZE"]) and \
                    (not used_feeder_ids.count(feeder_info[j]["FEEDER ID"])):
                row = [curr_job_data[i]["MANF PART NO"], feeder_info[j]["FEEDER SIZE"],
                       feeder_info[j]["FEEDER ID"], curr_job_data[i]["TAPE WIDTH"]]

                used_feeder_ids.append(feeder_info[j]["FEEDER ID"])
                break
        matched_job_data.append(row)

    return matched_job_data


# Writes sync'd job data
# MANF PART NO, FEEDER WIDTH, FEEDER ID	SLOT
def write_syncd_job_data(loc, data):
    with open(loc, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["MANF PART NO", "FEEDER WIDTH", "FEEDER ID", "SLOT"])

        for i in data:
            writer.writerow(i)


def main_window_layout():
    sg.theme('Dark Grey 4')

    layout = [[sg.Text('Input VIOS TEXT file:', size=(26, 1)), sg.InputText(size=(60, 1), key='-INPUT FILE-'),
               sg.FileBrowse(initial_folder=os.getcwd())],

              [sg.Text('Output extracted job data location:', size=(26, 1)),
               sg.InputText(default_text=os.getcwd(), size=(60, 1), key='-OUTPUT EXTRACTED JOB DATA-'),
               sg.FolderBrowse(initial_folder=os.getcwd())],

              [sg.Button(button_text='Parse', size=(10, 1)), sg.Text(size=(40, 1), key="-PARSE STATUS-")],

              [sg.Text('-' * 176)],

              [sg.Text('Input physical feeder data CSV:', size=(26, 1)), sg.InputText(
                  size=(60, 1), key='-AVAIL FEEDERS-'), sg.FileBrowse()],

              [sg.Text('Output matched data folder:', size=(26, 1)),
               sg.InputText(size=(60, 1), key='-FEEDER DATA-', default_text=os.getcwd()),
               sg.FolderBrowse(initial_folder=os.getcwd())],

              [sg.Button(button_text='Generate matched data'), sg.Text(size=(40, 1), key="-MATCHED DATA STATUS-")],

              [sg.Text('-' * 176)],

              [sg.Button(button_text='Enter verify mode')]
              ]

    return sg.Window('Feeder-Parts-System', layout).Finalize()


def verify_window_layout():
    sg.theme('Dark Grey 4')
    layout = [[sg.Button("Scan a part", size=(80, 40), button_color=("black", "#ff8400"), pad=(400, 10),
                         disabled=False, key="-MAIN_BUTTON-", font=("Helvetica", 35))],

              ]
    return sg.Window(title='Feeder-Parts-System', return_keyboard_events=True,
                     layout=layout, use_default_focus=False, size=(1500, 800)).Finalize()


# Uses a dict to map what char should be used when shift key is held
def shift_key_map(char):
    switch = {
        "1": "!",
        "2": "@",
        "3": "#",
        "4": "$",
        "5": "%",
        "6": "^",
        "7": "&",
        "8": "*",
        "9": "(",
        "0": ")",
        "-": "_",
        "=": "+",
        "[": "{",
        "]": "}",
        ";": ":",
        "\'": "\"",
        ",": "<",
        ".": ">",
        "/": "?",
        "q": "Q",
        "w": "W",
        "e": "E",
        "r": "R",
        "t": "T",
        "y": "Y",
        "u": "U",
        "i": "I",
        "o": "O",
        "p": "P",
        "a": "A",
        "s": "S",
        "d": "D",
        "f": "F",
        "g": "G",
        "h": "H",
        "j": "J",
        "k": "K",
        "l": "L",
        "z": "Z",
        "x": "X",
        "c": "C",
        "v": "V",
        "b": "B",
        "n": "N",
        "m": "M"
    }

    return switch.get(char, "?")


# Returns the feeder slot from the syncd job data based on manf part no
def get_feeder_slot(job_feeder_data_loc, part_no):
    with open(job_feeder_data_loc, newline='') as file:
        feeder_info = csv.DictReader(file, delimiter=',')
        for row in feeder_info:
            if row["MANF PART NO"] == part_no:
                return row["FEEDER SLOT"]


# Returns the feeder id from the syncd job data based on manf part no
def get_feeder_id(job_feeder_data_loc, part_no):
    with open(job_feeder_data_loc, newline='') as file:
        feeder_info = csv.DictReader(file, delimiter=',')
        for row in feeder_info:
            if row["MANF PART NO"] == part_no:
                return row["FEEDER ID"]

# GUI Helpers


def parse_data(win, win_vals):
    try:
        curr_file = open_vios_file(win_vals["-INPUT FILE-"])
        if valid_vios_file(curr_file):
            write_extracted_job_data(curr_file, win_vals['-OUTPUT EXTRACTED JOB DATA-'])
            win['-PARSE STATUS-'].update("File PARSED!")
        else:
            win['-PARSE STATUS-'].update("ERROR; NOT VIOS TXT FILE")
    except IndexError:
        win['-PARSE STATUS-'].update("ERROR; INVALID FILE")
    except FileNotFoundError:
        win['-PARSE STATUS-'].update("ERROR; PLEASE SELECT A VALID FILE")


def verify_gui(job_feeder_data_loc):
    verify_window = verify_window_layout()

    shift_hit = False
    val = ""
    part_scanned = False
    err = False
    time_since = time.time()
    while True:  # Event Loop
        event, values = verify_window.read(timeout=100, timeout_key="-TIMEOUT-")

        if event == "-TIMEOUT-":
            if err:
                winsound.PlaySound("SystemHand", winsound.SND_ALIAS)
                err = False
            if ((time.time() - time_since) > 0.1) & (val != ""):
                ecia_data = extract_ecia_2d_code(val)
                val = ""
                if ecia_data is None:
                    verify_window["-MAIN_BUTTON-"].update(button_color=("black", "red"))
                    verify_window["-MAIN_BUTTON-"].update("ERROR: INVALID ECIA DATA")
                    err = True
                    continue
                supplier_part_no = ecia_data["supplier_part_number"]
                if supplier_part_no is None:
                    verify_window["-MAIN_BUTTON-"].update(button_color=("black", "red"))
                    verify_window.FindElement("-MAIN_BUTTON-").update("ERROR: NO PART NO FOUND")
                    err = True
                else:
                    feeder_id = get_feeder_id(job_feeder_data_loc, supplier_part_no)
                    if feeder_id is None:
                        verify_window["-MAIN_BUTTON-"].update(button_color=("black", "red"))
                        verify_window["-MAIN_BUTTON-"].update("PART: " + supplier_part_no +
                                                              "\n ERROR: NOT IN JOB DATA")
                        err = True

                    else:
                        verify_window["-MAIN_BUTTON-"].update(button_color=("black", "#ff8400"))
                        verify_window["-MAIN_BUTTON-"].update("PART: " + supplier_part_no +
                                                              "\n FEEDER ID: " + feeder_id)
                        part_scanned = True
            continue

        if event == sg.WIN_CLOSED or event == 'Exit':
            break

        if event == "-MAIN_BUTTON-":
            continue

        if event == "Shift_L:16":
            shift_hit = True
            time_since = time.time()
            continue

        if shift_hit:
            val = val + shift_key_map(event)
            time_since = time.time()
            shift_hit = False
        else:
            time_since = time.time()
            val = val + event

    verify_window.close()


# Main run method
def run_gui():
    matched_data_loc = ""
    window = main_window_layout()
    while True:  # Event Loop
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Exit':
            break

        if event == "Parse":
            parse_data(window, values)

        if event == "Generate matched data":
            matched_data_loc = values['-OUTPUT EXTRACTED JOB DATA-'] + "\extracted_job_data.csv"
            job_feeder_data = gen_syncd_job_data(values['-AVAIL FEEDERS-'], matched_data_loc)

            job_feeder_loc = values['-FEEDER DATA-'] + "\sync_job_data.csv"
            write_syncd_job_data(job_feeder_loc, job_feeder_data)
            window['-MATCHED DATA STATUS-'].update("Matched data generated!")

        if event == "Enter verify mode":
            job_feeder_data_loc = values['-FEEDER DATA-'] + "\sync_job_data.csv"
            window.close()
            verify_gui(job_feeder_data_loc)

    window.close()


def valid_ecia_2d_code(code):
    return "[)>{RS}06{GS}" in code


def remove_prefix(text, prefix):
    return text[text.startswith(prefix) and len(prefix):]


def return_ecia_fields(line):
    data_identifiers = ["1T", "1P", "6D", "4L", "P", "Q", "9D", "10D"]
    field_names = ["lot_code", "supplier_part_number", "ship_date",
                   "country_of_origin", "customer_part_number", "Quantity", "date_code_1", "date_code_2"]

    for i in range(0, len(data_identifiers)):
        if str(line).startswith(data_identifiers[i]):
            return field_names[i], remove_prefix(line, data_identifiers[i])
    return None


def extract_ecia_2d_code(code):
    if not valid_ecia_2d_code(code):
        return None

    try:
        temp_dict = {}
        temp = str(code).split("{GS}")
        temp.remove("[)>{RS}06")
    except ValueError:
        return None

    for val in temp:
        extracted = return_ecia_fields(val)
        if extracted:
            temp_dict[extracted[0]] = extracted[1]

    return temp_dict


run_gui()
