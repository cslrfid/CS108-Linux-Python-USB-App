import Constants

def GetVersion():

    buffer = bytearray(10)

    # header
    buffer[0] = Constants.PREFIX
    buffer[1] = Constants.CONNECTION_USB
    buffer[2] = 2 # payload length
    buffer[3] = Constants.TYPE_BT
    buffer[4] = Constants.RESERVE
    buffer[5] = Constants.LINK_DOWN
    buffer[6] = 0
    buffer[7] = 0

    # payload
    buffer[8] = 0xC0
    buffer[9] = 0x00

    return bytes(buffer)


def SendImageData(subpart_data, subpart):
    buffer = bytearray(78)
    total_subpart = Constants.BT_IMAGE_TOTAL_SUBPART

    # header
    buffer[0] = Constants.PREFIX
    buffer[1] = Constants.CONNECTION_USB
    buffer[2] = 70 #payload length
    buffer[3] = Constants.TYPE_BT
    buffer[4] = Constants.RESERVE
    buffer[5] = Constants.LINK_DOWN
    buffer[6] = 0
    buffer[7] = 0
    # payload
    buffer[8] = 0xC0
    buffer[9] = 0x01
    buffer[10] = (total_subpart >> 8) & 0xFF
    buffer[11] = total_subpart & 0xFF
    buffer[12] = (subpart >> 8) & 0xFF
    buffer[13] = subpart & 0xFF

    for i in range(0, len(subpart_data)):
        buffer[i + 14] = subpart_data[i]

    return bytes(buffer)
