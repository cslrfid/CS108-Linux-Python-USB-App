import Constants

# RFID module commands, ported from CSL's CS108 PC Demo App (RFIDCommands.cs).
# MAC/OEM/NV-update commands are 8-byte RFID packets carried inside a CS108
# packet with payload 0x80 0x02 (see SendData).

def _GenerateCrc32Table():
    table = []
    for i in range(256):
        c = i << 24
        for _ in range(8):
            if c & 0x80000000:
                c = ((c << 1) ^ 0x04C11DB7) & 0xFFFFFFFF
            else:
                c = (c << 1) & 0xFFFFFFFF
        table.append(c)
    return table

crc32_table = _GenerateCrc32Table()

def FastCrc32(crc, buffer, offset, length):
    for i in range(offset, offset + length):
        crc = crc32_table[((crc >> 24) ^ buffer[i]) & 0xFF] ^ ((crc << 8) & 0xFFFFFFFF)
    return crc

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

def SendData(data):
    buffer = bytearray(len(data) + 10)

    # header
    buffer[0] = Constants.PREFIX
    buffer[1] = Constants.CONNECTION_USB
    buffer[2] = len(data) + 2 #payload length
    buffer[3] = Constants.TYPE_RFID
    buffer[4] = Constants.RESERVE
    buffer[5] = Constants.LINK_DOWN
    buffer[6] = 0
    buffer[7] = 0
    # payload
    buffer[8] = 0x80
    buffer[9] = 0x02
    buffer[10:] = data

    return bytes(buffer)

# The functions below return a list of CS108 packets to transmit in order

def GetVersion():
    return [SendData(bytes([0x70, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]))]

def WriteOEM(address, data):
    return [SendData(bytes([0x70, 0x01, 0x00, 0x05, address & 0xFF, (address >> 8) & 0xFF, 0x00, 0x00])),
            SendData(bytes([0x70, 0x01, 0x01, 0x05, data & 0xFF, (data >> 8) & 0xFF, (data >> 16) & 0xFF, (data >> 24) & 0xFF])),
            SendData(bytes([0x70, 0x01, 0x00, 0xF0, 0x02, 0x00, 0x00, 0x00]))]

def ReadOEM(address):
    return [SendData(bytes([0x70, 0x01, 0x00, 0x05, address & 0xFF, (address >> 8) & 0xFF, 0x00, 0x00])),
            SendData(bytes([0x70, 0x01, 0x00, 0xF0, 0x03, 0x00, 0x00, 0x00]))]

def Reset():
    return [SendData(bytes([0x40, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]))]

def StartNVMemUpdate():
    return [SendData(bytes([0x70, 0x01, 0x00, 0xF0, 0x01, 0x00, 0x00, 0x00]))]

def UpdateComplete():
    return [SendData(bytes([0x0D, 0xF0, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00]))]

def SendImageData(subpart_data, block):
    buffer = bytearray(52)
    addr = 0x00106000 + (32 * block)

    # NV Mem Update Range Packet Fields
    buffer[0] = 0x0D
    buffer[1] = 0xF0
    buffer[2] = 0x01
    buffer[3] = 0x00
    buffer[4] = 0x0B
    buffer[5] = 0x00
    buffer[6] = 0x00
    buffer[7] = 0x00
    buffer[8] = addr & 0xFF
    buffer[9] = (addr >> 8) & 0xFF
    buffer[10] = (addr >> 16) & 0xFF
    buffer[11] = (addr >> 24) & 0xFF
    # bytes 12-15: CRC, bytes 16-19: test mode (0)
    buffer[20:20 + len(subpart_data)] = subpart_data

    crc = FastCrc32(0, buffer, 0, 12)
    crc = FastCrc32(crc, buffer, 16, 36)

    buffer[12] = crc & 0xFF
    buffer[13] = (crc >> 8) & 0xFF
    buffer[14] = (crc >> 16) & 0xFF
    buffer[15] = (crc >> 24) & 0xFF

    return [SendData(buffer)]
