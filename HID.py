import ctypes
import BTCommands

# USB Parameters
VID = 0x10C4
PID = 0x8468
HID_READ_TIMEOUT = 0
HID_WRITE_TIMEOUT = 1000

# HID Report IDs
ID_IN_CONTROL = 0xFE
ID_OUT_CONTROL = 0xFD
ID_IN_DATA = 0x01
ID_OUT_DATA = 0x02

# HID Report Sizes
SIZE_IN_CONTROL = 5
SIZE_OUT_CONTROL = 5
SIZE_IN_DATA = 61
SIZE_OUT_DATA = 61
SIZE_MAX_WRITE = 59
SIZE_MAX_READ = 59

# Return Codes
HID_DEVICE_SUCCESS = 0x00
HID_DEVICE_NOT_FOUND = 0x01
HID_DEVICE_NOT_OPENED = 0x02
HID_DEVICE_ALREADY_OPENED = 0x03
HID_DEVICE_TRANSFER_TIMEOUT = 0x04
HID_DEVICE_TRANSFER_FAILED = 0x05
HID_DEVICE_CANNOT_GET_HID_INFO = 0x06
HID_DEVICE_HANDLE_ERROR = 0x07
HID_DEVICE_INVALID_BUFFER_SIZE = 0x08
HID_DEVICE_SYSTEM_CODE = 0x09
HID_DEVICE_UNSUPPORTED_FUNCTION = 0x0A
HID_DEVICE_UNKNOWN_ERROR = 0xFF

# String Types
HID_VID_STRING = 0x01
HID_PID_STRING = 0x02
HID_PATH_STRING = 0x03
HID_SERIAL_STRING = 0x04
HID_MANUFACTURER_STRING = 0x05
HID_PRODUCT_STRING = 0x06
MAX_PATH_LENGTH = 260

MAX_REPORT_REQUEST_XP = 512

_mod = ctypes.cdll.LoadLibrary('libslabhiddevice.so')

HidDevice_GetNumHidDevices = _mod.HidDevice_GetNumHidDevices
HidDevice_GetNumHidDevices.argtypes = (ctypes.c_int, ctypes.c_int)
HidDevice_GetNumHidDevices.restype = ctypes.c_int

HidDevice_GetMaxReportRequest = _mod.HidDevice_GetMaxReportRequest
HidDevice_GetMaxReportRequest.argtypes = (ctypes.c_void_p,)
HidDevice_GetMaxReportRequest.restype = ctypes.c_int

HidDevice_GetHidString = _mod.HidDevice_GetHidString
HidDevice_GetHidString.argtypes = (ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_byte, ctypes.c_char_p, ctypes.c_int)
HidDevice_GetHidString.restype = ctypes.c_byte

HidDevice_GetString = _mod.HidDevice_GetString
HidDevice_GetString.argtypes = (ctypes.c_void_p, ctypes.c_byte, ctypes.c_int)
HidDevice_GetString.restype = ctypes.c_byte

HidDevice_Open = _mod.HidDevice_Open
HidDevice_Open.argtypes = (ctypes.POINTER(ctypes.c_void_p), ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int)
HidDevice_Open.restype = ctypes.c_byte

HidDevice_SetTimeouts = _mod.HidDevice_SetTimeouts
HidDevice_SetTimeouts.argtypes = (ctypes.c_void_p, ctypes.c_int, ctypes.c_int)
HidDevice_SetTimeouts.restype = None

HidDevice_Close = _mod.HidDevice_Close
HidDevice_Close.argtypes = (ctypes.c_void_p,)
HidDevice_Close.restype = ctypes.c_int

HidDevice_IsOpened = _mod.HidDevice_IsOpened
HidDevice_IsOpened.argtypes = (ctypes.c_void_p,)
HidDevice_IsOpened.restype = ctypes.c_bool

HidDevice_SetOutputReport_Interrupt = _mod.HidDevice_SetOutputReport_Interrupt
HidDevice_SetOutputReport_Interrupt.argtypes = (ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int)
HidDevice_SetOutputReport_Interrupt.restype = ctypes.c_byte 

HidDevice_GetInputReport_Interrupt = _mod.HidDevice_GetInputReport_Interrupt
HidDevice_GetInputReport_Interrupt.argtypes = (ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int))
HidDevice_GetInputReport_Interrupt.restype = ctypes.c_byte 

HidDevice_GetOutputReportBufferLength = _mod.HidDevice_GetOutputReportBufferLength
HidDevice_GetOutputReportBufferLength.argtypes = (ctypes.c_void_p,)
HidDevice_GetOutputReportBufferLength.restype = ctypes.c_int16


def GetNumHidDevices():
    return HidDevice_GetNumHidDevices(VID, PID)

def GetMaxReportRequest(device):
    return HidDevice_GetMaxReportRequest(device)

def GetHidString(deviceIndex):
    pnt = bytes(MAX_PATH_LENGTH) 
    status = HidDevice_GetHidString(deviceIndex, VID, PID, HID_PATH_STRING, pnt, MAX_PATH_LENGTH)
    if status == HID_DEVICE_SUCCESS:
        return pnt.decode("utf-8")
    return ""

def Open(deviceIndex):
    handle = ctypes.c_void_p(0)

    status = HidDevice_Open(ctypes.byref(handle), deviceIndex, VID, PID, MAX_REPORT_REQUEST_XP)
    if status == HID_DEVICE_SUCCESS:
        HidDevice_SetTimeouts(handle, HID_READ_TIMEOUT, HID_WRITE_TIMEOUT)
        return handle.value
    return None

def Close(handle):
    hdl = ctypes.c_void_p(handle)

    if HidDevice_Close(hdl) == HID_DEVICE_SUCCESS:
        return True
    else:
        return False

def IsOpen(handle):
    hdl = ctypes.c_void_p(handle)
    return HidDevice_IsOpened(hdl)

def TransmitData(handle, buffer):
    hdl = ctypes.c_void_p(handle)

    success = False
    reportSize = HidDevice_GetOutputReportBufferLength(hdl)
    report = bytearray(reportSize)

    if reportSize >= SIZE_OUT_DATA:
        bytesWritten = 0
        bytesToWrite = len(buffer)

        pnt = bytes(reportSize)

        while bytesWritten < bytesToWrite:
            transferSize = min(bytesToWrite - bytesWritten, SIZE_MAX_WRITE)
            report = bytearray(reportSize)
            report[0] = ID_OUT_DATA
            report[1] = transferSize
            report[2:2+transferSize] = buffer[bytesWritten:bytesWritten+transferSize]
            # pnt = ctypes.cast(bytes(report), ctypes.POINTER(ctypes.c_byte))
            if HidDevice_SetOutputReport_Interrupt(hdl, bytes(report), reportSize) != HID_DEVICE_SUCCESS:
                # Stop transmitting if there was an error
                break

            bytesWritten += transferSize

        # Write completed successfully
        if bytesWritten == bytesToWrite:    
            success = True
		        
    return success

def ReceiveData(handle, bufferSize):
    hdl = ctypes.c_void_p(handle)

    success = False
    buffer = bytearray(bufferSize)
    bytesRead = 0

    reportSize = HidDevice_GetOutputReportBufferLength(hdl)
    if bufferSize >= SIZE_MAX_READ:
        numReports = int(bufferSize / SIZE_MAX_READ)
        reportBufferSize = numReports * reportSize
        reportBuffer = bytearray(reportBufferSize)
        reportBufferRead = ctypes.c_int()
        
        pnt = bytes(reportBufferSize)
        status = HidDevice_GetInputReport_Interrupt(hdl, pnt, reportBufferSize, numReports, reportBufferRead)
        if status == HID_DEVICE_SUCCESS or status == HID_DEVICE_TRANSFER_TIMEOUT:
            reportBuffer[:reportBufferSize] = pnt[:reportBufferSize]
            
            for i in range(0, reportBufferRead.value, reportSize):
                bytesInReport = reportBuffer[i + 1]
                buffer[bytesRead:bytesRead+bytesInReport] = reportBuffer[i+2:i+2+bytesInReport]
                bytesRead += bytesInReport

            success = True
    return success, bytes(buffer[:bytesRead])


def main():
    # Module unit testing
    handle = 0

    NumOfConnectedDevices = GetNumHidDevices()
    print("CS108 USB library loaded: ", _mod)
    print("Number of USB device(s) connected: ", NumOfConnectedDevices)
    for i in range(NumOfConnectedDevices):
        print("Device {}: HIDString={}".format(i, GetHidString(i)))      
    
    if NumOfConnectedDevices > 0:
        handle = Open(0)
        if handle != None:
            print("Device 0 opened: {}".format(handle))
        else:
            print("Unable to open device 0")
            return
    
        print("Get BT firmware version")
        command = BTCommands.GetVersion()

        if not TransmitData(handle, command):
            print("Device failed to transmit data.")
        else:
            bufferSize = GetMaxReportRequest(handle) * SIZE_MAX_READ
            status, result = ReceiveData(handle, bufferSize)
            if not status:
                print("Device failed to receive data.")
                return
            else:
                print("Received Data: {}".format(result.hex().upper()))

        if Close(handle):
            print("Device 0 closed")
        else:
            print("Unable to close device 0")

if __name__ == '__main__':
        main()