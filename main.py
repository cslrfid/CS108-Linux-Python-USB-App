import HID
import CS108FwUpgrade
import sys
import os

def main():
    
    handle = 0
    print("----------------------------")
    print("CS108 Firmware Upgrade Toool")
    print("----------------------------")

    if (len(sys.argv) < 3) or (sys.argv[1].lower() != "/b" and sys.argv[1].lower() != "/n" and sys.argv[1].lower() != "/r"):
        print("Usage: python main.py [ /B | /N | /R ] file")
        return
    
    if not os.path.exists(sys.argv[2]):
        print("File specificed ({}) not found".format(sys.argv[2]))
        return
    
    NumOfConnectedDevices = HID.GetNumHidDevices()
    print("Number of USB device(s) connected: ", NumOfConnectedDevices)
    for i in range(NumOfConnectedDevices):
        print("Device {}: {}".format(i, HID.GetHidString(i)))      
    
    if NumOfConnectedDevices > 0:
        print("Open the first device found...")
        handle = HID.Open(0)
        if handle != None:
            print("Device opened: handle={}".format(handle))
        else:
            print("Unable to open device")
            return
    else:
        print("No CS108 device connected")
        return

    if sys.argv[1].lower() == "/b":
        btVersion=CS108FwUpgrade.GetBTVersion(handle)
        print("Current Bluetooth firmware version: {}".format(btVersion))

        fileName = sys.argv[2]
        print("Upgrade Bluetooth firmware with file:", fileName)
        in_file = open(fileName, "rb") # opening for [r]eading as [b]inary
        stream = in_file.read()
        in_file.close()

        if CS108FwUpgrade.UpdateBTImage(handle, stream):
            print("Bluetooth firmware upgrade successful")
        else:
            print("Bluetooth firmware upgrade failed")
        
        HID.Close(handle)
    elif sys.argv[1].lower() == "/n":
        slVersion=CS108FwUpgrade.GetSLVersion(handle)
        print("Current Silicon Labs (network processor) firmware version: {}".format(slVersion))

        fileName = sys.argv[2]
        print("Upgrade Silicon Labs (network processor) firmware with file:", fileName)
        in_file = open(fileName, "rb") # opening for [r]eading as [b]inary
        stream = in_file.read()
        in_file.close()

        if CS108FwUpgrade.UpdateSilabImage(handle, stream):
            print("Silicon Labs (network processor) firmware upgrade successful")
        else:
            print("Silicon Labs (network processor) firmware upgrade failed")
        
        HID.Close(handle)
 
if __name__ == '__main__':
    main()