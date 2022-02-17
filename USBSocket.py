import time
from datetime import datetime
import HID
import BTCommands

def TransmitData(handle, buffer):
    success = False

    if (HID.IsOpen(handle)):
        try:
            success = HID.TransmitData(handle, buffer)

        except:
            print("USBSocket: Transmission error")
            success = False
    else:
        print("USBSocket: Transmission error")
        success = False
    
    return success

    
def ReceiveData(handle, bufferSize, timeout):
    success = False

    try:
        bytesRead = 0
        timer = time.monotonic()
        while bytesRead == 0:
            success, result = HID.ReceiveData(handle, bufferSize)
            bytesRead = len(result)
            timeElapsed = (time.monotonic() - timer) * 1000 
            if (not success) or (timeElapsed > timeout):
                print("USBSocket: recive timeout")
                success = False
                break
            time.sleep(BTCommands.TIMER_READ * 0.001)
    except:
        print("USBSocket: failed receiving data")
        success = False
    
    return success, result

