from time import time
import BTCommands
import USBSocket
import CRC
import HID

def GetBTVersion(handle):
    command = BTCommands.GetVersion()

    if not USBSocket.TransmitData(handle, command):
        print("Device failed to transmit data.")
        return ""

    if HID.IsOpen(handle):
        status, buffer = USBSocket.ReceiveData(handle, 128, 2000)
        if status:
            if (buffer[0] == BTCommands.PREFIX) and (len(buffer) >= 13) and (buffer[8] == 0xC0) and (buffer[9] == 0x00):
                crc = (buffer[6] << 8) | buffer[7]

                if (crc != 0) and (not CRC.CheckCRC(buffer, 0, 13, crc)):  
                    print("Wrong CRC received")
                    return ""

                btVersion = "{}.{}.{}".format(buffer[10],buffer[11],buffer[12])
                return btVersion
        else:
            print("Cannot get bluetooth firmware version")
            return ""
    else:
        print("Device is not connected.");
        return ""

def UpdateBTImage(handle, stream):
    if len(stream) != BTCommands.BT_IMAGE_SIZE:
        print("Incorrect image file size.")
        return False

    subpart = 1
    subpartBuffer = bytes(64)
    command = bytes()
    retry = 0

    print("\n")
    while True:
        if retry == 0:
            if len(stream) >=64:
                subpartBuffer = stream[0:64]
                stream = stream[64:]

        if len(subpartBuffer) > 0:
            command = BTCommands.SendImageData(subpartBuffer, subpart)
        else:
            print("Not enough image data.")
            return False

        if not USBSocket.TransmitData(handle, command):
            print("Device failed to transmit data.")
            return False

        if HID.IsOpen(handle):
            readBuffer = bytes(128)
            status, readBuffer = USBSocket.ReceiveData(handle, len(readBuffer), 5000)
            if status:
                if (readBuffer[0] == BTCommands.PREFIX) and (len(readBuffer) >= 11) and (readBuffer[8] == 0xC0) and (readBuffer[9] == 0x01):
                    if readBuffer[10] == 1:
                        print("Bluetooth firmwarwe Update Fail")
                        return False
                    elif readBuffer[10] == 2:
                        print("Bluetooth firmwarwe Update Successfull.  Wait for 15 seconds")
                        time.sleep(10)
                        return True
                    else:
                        print("\rCompleted: {0:3.1f}%".format((subpart * 100) / BTCommands.BT_IMAGE_TOTAL_SUBPART), end="")
                        subpart+=1
                        retry = 0
                else:
                    retry+=1
            else:
                retry+=1
        else:
            print("Device is not connected.")
            return False


                    