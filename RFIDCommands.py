import Constants

def PowerOn(on):
    buffer = bytearray(10)

    # header
    buffer[0] = Constants.PREFIX
    buffer[1] = Constants.CONNECTION_USB
    buffer[2] = 2 #payload length
    buffer[3] = Constants.TYPE_RFID
    buffer[4] = Constants.RESERVE
    buffer[5] = Constants.LINK_DOWN
    buffer[6] = 0
    buffer[7] = 0
    # payload
    buffer[8] = 0x80
    if on:
        buffer[9] = 0x00
    else:
        buffer[9] = 0x01
    
    return bytes(buffer)