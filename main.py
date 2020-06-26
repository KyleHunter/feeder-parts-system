TEXT_FILE_LOCATION = "BBS_PAD_LED_NEW.txt"
VALIDATION_LINE = 2
VALIDATION_TEXT = "&I.COMMENT=Philips_EMT_bv"

with open(TEXT_FILE_LOCATION) as file:  # Use file to refer to the file object
    data = file.readlines()


# Returns true if we are in a valid VIOS txt file
def valid_file():
    return VALIDATION_TEXT in data[VALIDATION_LINE]

# Returns a 2D array of feeder data: [i, j]
# i is part number
# j is un formatted lines of the parts feeder info
def get_feeder_data():
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


val = get_feeder_data()
for i in val[0]:
        print(repr(i))
