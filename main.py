import HID
import CS108FwUpgrade
import sys

def main():
    
    handle = 0
    print("CS108 Bluetooth Firmware Upgrade Toool")

    if (len(sys.argv) < 3):
        print("Usage: python main.py [ /B | /N | /R ] file_path")
        return

    if sys.argv[1].lower() == "/b":
        NumOfConnectedDevices = HID.GetNumHidDevices()
        print("Number of USB device(s) connected: ", NumOfConnectedDevices)
        for i in range(NumOfConnectedDevices):
            print("Device {}: HIDString={}".format(i, HID.GetHidString(i)))      
        
        if NumOfConnectedDevices > 0:
            print("Open the first device found...")
            handle = HID.Open(0)
            if handle != None:
                print("Device opened: {}".format(handle))
            else:
                print("Unable to open device")
                return
        else:
            print("No CS108 device connected.  Exit program")
            return

        print("Get BT firmware version")
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
    else:
        print("Usage: python main.py [ /B | /N | /R ] file_path")

 
if __name__ == '__main__':
    main()