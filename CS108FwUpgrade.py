import BTCommands
import SLCommands
import USBSocket
import CRC
import HID
import utils
import Constants

def GetBTVersion(handle):
    command = BTCommands.GetVersion()

    if not USBSocket.TransmitData(handle, command):
        print("Device failed to transmit data.")
        return ""

    if HID.IsOpen(handle):
        status, buffer = USBSocket.ReceiveData(handle, 128, 2000)
        if status:
            if (buffer[0] == Constants.PREFIX) and (len(buffer) >= 13) and (buffer[8] == 0xC0) and (buffer[9] == 0x00):
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
    if len(stream) != Constants.BT_IMAGE_SIZE:
        print("Incorrect image file size.")
        return False

    subpart = 1
    subpartBuffer = bytes(64)
    command = bytes()
    retry = 0

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
                if (readBuffer[0] == Constants.PREFIX) and (len(readBuffer) >= 11) and (readBuffer[8] == 0xC0) and (readBuffer[9] == 0x01):
                    if readBuffer[10] == 1:
                        print("")
                        return False
                    elif readBuffer[10] == 2:
                        print("\rCompleted:100.0%")
                        utils.WaitForSeconds(15)
                        print("")
                        return True
                    else:
                        print("\rCompleted: {0:3.1f}%".format((subpart * 100) / Constants.BT_IMAGE_TOTAL_SUBPART), end="")
                        subpart+=1
                        retry = 0
                else:
                    retry+=1
            else:
                retry+=1
        else:
            print("Device is not connected.")
            return False


def UpdateSilabImage(handle, stream):
    if len(stream) != Constants.SILAB_IMAGE_SIZE:
        print("Incorrect image file size.")
        return False

    subpart = 1
    subpartBuffer = bytes(114)
    command = bytes()
    retry = 0

    while True:
        if retry == 0:
            if len(stream) >= 114:
                subpartBuffer = stream[0:114]
                stream = stream[114:]

        if len(subpartBuffer) > 0:
            command = SLCommands.SendImageData(subpartBuffer, subpart)
        else:
            print("Not enough image data.")
            return False

        if not USBSocket.TransmitData(handle, command):
            print("Device failed to transmit data.")
            return False

        if HID.IsOpen(handle):
            readBuffer = bytes(128)
            status, readBuffer = USBSocket.ReceiveData(handle, len(readBuffer), 1000)
            if status:
                if (readBuffer[0] == Constants.PREFIX) and (len(readBuffer) >= 11) and (readBuffer[8] == 0xB0) and (readBuffer[9] == 0x01):
                    if readBuffer[10] == 1:
                        print("")
                        return False
                    elif readBuffer[10] == 2:
                        print("\rCompleted:100.0%")
                        utils.WaitForSeconds(15)
                        print("")
                        return True
                    else:
                        print("\rCompleted: {0:3.1f}%".format((subpart * 100) / Constants.SILAB_IMAGE_SIZE), end="")
                        subpart+=1
                        retry = 0
                else:
                    retry+=1
            else:
                retry+=1
        else:
            print("Device is not connected.")
            return False        