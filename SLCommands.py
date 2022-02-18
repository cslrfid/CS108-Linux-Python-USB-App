import Constants


def SendImageData(subpart_data, subpart):
    buffer = bytearray(128)
    total_subpart = Constants.SILAB_IMAGE_TOTAL_SUBPART

    # header
    buffer[0] = Constants.PREFIX
    buffer[1] = Constants.CONNECTION_USB
    buffer[2] = 120 #payload length
    buffer[3] = Constants.TYPE_SILAB
    buffer[4] = Constants.RESERVE
    buffer[5] = Constants.LINK_DOWN
    buffer[6] = 0
    buffer[7] = 0
    # payload
    buffer[8] = 0xB0
    buffer[9] = 0x01
    buffer[10] = (total_subpart >> 8) & 0xFF
    buffer[11] = total_subpart & 0xFF
    buffer[12] = (subpart >> 8) & 0xFF
    buffer[13] = subpart & 0xFF

    for i in range(0, 114):
        buffer[i + 14] = subpart_data[i]

    return bytes(buffer)