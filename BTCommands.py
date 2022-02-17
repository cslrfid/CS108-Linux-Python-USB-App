


TIMER_READ = 1; # ms
        
SILAB_IMAGE_SIZE = 16384
SILAB_IMAGE_TOTAL_SUBPART = 144 # size/114+1
SILAB_BOOTLOADER_SIZE = 9216
SILAB_BOOTLOADER_TOTAL_SUBPART = 81 # size/114+1

BT_IMAGE_SIZE = 124928
BT_IMAGE_TOTAL_SUBPART = 1952 # size/64
BT_BOOTLOADER_SIZE = 4096
BT_BOOTLOADER_TOTAL_SUBPART = 64 # size/64

RFID_IMAGE_SIZE = 203776
RFID_IMAGE_TOTAL_SUBPART = 6368 # size/32
RFID_BOOTLOADER_SIZE = 24576
RFID_BOOTLOADER_TOTAL_SUBPART = 768 # size/32

PREFIX = 0xA7
CONNECTION_BT = 0xB3
CONNECTION_USB = 0xE6
TYPE_RFID = 0xC2
TYPE_BARCODE = 0x6A
TYPE_NOTIFY = 0xD9
TYPE_SILAB = 0xE8
TYPE_BT = 0x5F
LINK_DOWN = 0x37
LINK_UP = 0x9E
RESERVE = 0x82

def GetVersion():

    buffer = bytearray(10)

    # header
    buffer[0] = PREFIX
    buffer[1] = CONNECTION_USB
    buffer[2] = 2; # payload length
    buffer[3] = TYPE_BT
    buffer[4] = RESERVE
    buffer[5] = LINK_DOWN
    buffer[6] = 0
    buffer[7] = 0

    # payload
    buffer[8] = 0xC0
    buffer[9] = 0x00

    return bytes(buffer)


def SendImageData(subpart_data, subpart):
    buffer = bytearray(78)
    total_subpart = BT_IMAGE_TOTAL_SUBPART

    # header
    buffer[0] = PREFIX
    buffer[1] = CONNECTION_USB
    buffer[2] = 70 #payload length
    buffer[3] = TYPE_BT
    buffer[4] = RESERVE
    buffer[5] = LINK_DOWN
    buffer[6] = 0
    buffer[7] = 0
    # payload
    buffer[8] = 0xC0
    buffer[9] = 0x01
    buffer[10] = (total_subpart >> 8) & 0xFF
    buffer[11] = total_subpart & 0xFF
    buffer[12] = (subpart >> 8) & 0xFF
    buffer[13] = subpart & 0xFF

    for i in range(0, 64):
        buffer[i + 14] = subpart_data[i]

    return bytes(buffer)
