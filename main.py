import csv

# PARTS FEEDER SYSTEM

TEXT_FILE_LOCATION = "BBS_PAD_LED_NEW.txt"

with open(TEXT_FILE_LOCATION) as file:  # Use file to refer to the file object
    data = file.readlines()


# Returns true if we are in a valid VIOS txt file
def valid_file():
    return "&I.COMMENT=Philips_EMT_bv" in data[2]


# Returns a 2D array of raw feeder data: [i, j]
# i is index
# j is un-formatted lines of the parts feeder info
def get_raw_feeder_data():
    fd_data = 0
    res = []
    res_internal = []
    first_line = 1
    i = 0
    for line in data:
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
# j is [Manf. part no, raw feeder type, feeder slot]
def extract_feeder_data():
    raw = get_raw_feeder_data()
    res = []
    for i in raw:
        res_internal = [i[1].split('    ', 1)[0].strip(), i[3][2:4].strip()]
        f_slot = int(i[5].split('     ')[2].strip())
        if f_slot < 64:
            f_slot += 1
        if f_slot > 64:
            f_slot += 37

        res_internal.append(str(f_slot))  # Raw feeder slot
        res.append(res_internal)
    return res


# Writes formatted feeder data to output.csv
def write_output():
    with open('output.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["MANF PART NO", "FEEDER TYPE", "FEEDER SLOT"])
        val = extract_feeder_data()
        for i in val:
            writer.writerow(i)


write_output()
