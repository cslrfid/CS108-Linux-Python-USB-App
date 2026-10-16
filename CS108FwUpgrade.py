import time
import BTCommands
import SLCommands
import RFIDCommands
import USBSocket
import CRC
import HID
import utils
import Constants

# Consecutive bad/missing replies tolerated for one subpart before giving up
MAX_RETRY = 10

# Seconds to wait after a successful upload while the processor restarts
SILAB_RESTART_WAIT = 5
BT_RESTART_WAIT = 15
RFID_RESTART_WAIT = 6

# RFID NV memory update status codes (index = status value)
NV_STATUS = [
    "NVMEMUPD_STAT_UPD_SUCCESS",
    "NVMEMUPD_STAT_RESERVED_01",
    "NVMEMUPD_STAT_WR_FAIL",
    "NVMEMUPD_STAT_UNK_CMD",
    "NVMEMUPD_STAT_CMD_IGN",
    "NVMEMUPD_STAT_BNDS",
    "NVMEMUPD_STAT_MAGIC",
    "NVMEMUPD_STAT_PKTLEN",
    "NVMEMUPD_STAT_EXIT_ERR",
    "NVMEMUPD_STAT_EXIT_SUCCESS",
    "NVMEMUPD_STAT_EXIT_NOWRITES",
    "NVMEMUPD_STAT_GEN_RXPKT_ERR",
    "NVMEMUPD_STAT_RESERVED_02",
    "NVMEMUPD_STAT_INT_MEM_BNDS",
    "NVMEMUPD_STAT_ENTRY_OK",
    "NVMEMUPD_STAT_RXPKT_MAX",
    "NVMEMUPD_STAT_RX_TO",
    "NVMEMUPD_STAT_CRC_ERR",
]

def PrintProgress(percent):
    print("\rCompleted: {0:5.1f}%".format(percent), end="\n" if percent >= 100 else "")

def _ReceiveReply(handle, code, timeout):
    # Wait up to timeout (ms) for the CS108 packet whose payload starts with the
    # 2-byte command code, skipping unrelated packets that can arrive in between,
    # such as notifications (type 0xD9, e.g. event 0xA101 "error code 0").
    buffer = bytearray()
    deadline = time.monotonic() + timeout / 1000
    while time.monotonic() < deadline:
        remaining = max(1, (deadline - time.monotonic()) * 1000)
        status, data = USBSocket.ReceiveData(handle, 128, remaining)
        if not status:
            return False, b""
        buffer += data
        while len(buffer) >= 8:
            if buffer[0] != Constants.PREFIX:
                del buffer[0] # resync on the next prefix byte
                continue
            total = buffer[2] + 8
            if len(buffer) < total:
                break
            frame = bytes(buffer[:total])
            del buffer[:total]
            if total >= 10 and frame[8] == code[0] and frame[9] == code[1]:
                return True, frame
    return False, b""

def GetBTVersion(handle, log=print):
    command = BTCommands.GetVersion()

    if not USBSocket.TransmitData(handle, command):
        log("Device failed to transmit data.")
        return ""

    if HID.IsOpen(handle):
        status, buffer = _ReceiveReply(handle, (0xC0, 0x00), 2000)
        if status:
            if (buffer[0] == Constants.PREFIX) and (len(buffer) >= 13) and (buffer[8] == 0xC0) and (buffer[9] == 0x00):
                crc = (buffer[6] << 8) | buffer[7]

                if (crc != 0) and (not CRC.CheckCRC(buffer, 0, 13, crc)):
                    log("Wrong CRC received")
                    return ""

                btVersion = "{}.{}.{}".format(buffer[10],buffer[11],buffer[12])
                return btVersion
        log("Cannot get bluetooth firmware version")
        return ""
    else:
        log("Device is not connected.")
        return ""

def GetSLVersion(handle, log=print):

    command = RFIDCommands.PowerOn(True)

    if not USBSocket.TransmitData(handle, command):
        log("Device failed to transmit data.")
        return ""

    if HID.IsOpen(handle):
        _ReceiveReply(handle, (0x80, 0x00), 2000)
    else:
        log("Device is not connected.")
        return ""

    command = SLCommands.GetVersion()

    if not USBSocket.TransmitData(handle, command):
        log("Device failed to transmit data.")
        return ""

    if HID.IsOpen(handle):
        status, buffer = _ReceiveReply(handle, (0xB0, 0x00), 1000)
        if status:
            if (buffer[0] == Constants.PREFIX) and (len(buffer) >= 13) and (buffer[8] == 0xB0) and (buffer[9] == 0x00):
                slVersion = "{}.{}.{}".format(buffer[10],buffer[11],buffer[12])
                return slVersion
        log("Cannot get Silicon Labs (network processor) firmware version")
        return ""
    else:
        log("Device is not connected.")
        return ""

def UpdateBTImage(handle, stream, log=print, progress=PrintProgress, tick=None):
    if len(stream) != Constants.BT_IMAGE_SIZE:
        log("Incorrect image file size.")
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
            else:
                subpartBuffer = stream[0:]
                stream = stream[0:]
        elif retry > MAX_RETRY:
            log("No valid reply from the reader for block {} after {} retries.".format(subpart, MAX_RETRY))
            return False

        if len(subpartBuffer) > 0:
            command = BTCommands.SendImageData(subpartBuffer, subpart)
        else:
            log("Not enough image data.")
            return False

        if not USBSocket.TransmitData(handle, command):
            log("Device failed to transmit data (block {} of {}).".format(subpart, Constants.BT_IMAGE_TOTAL_SUBPART))
            return False

        if HID.IsOpen(handle):
            readBuffer = bytes(128)
            status, readBuffer = _ReceiveReply(handle, (0xC0, 0x01), 5000)
            if status:
                if (readBuffer[0] == Constants.PREFIX) and (len(readBuffer) >= 11) and (readBuffer[8] == 0xC0) and (readBuffer[9] == 0x01):
                    if readBuffer[10] == 1:
                        log("The reader reported a Bluetooth upgrade failure at block {}.".format(subpart))
                        return False
                    elif readBuffer[10] == 2:
                        progress(100.0)
                        log("Upload complete.")
                        utils.WaitForSeconds(BT_RESTART_WAIT, tick)
                        log("")
                        return True
                    else:
                        progress((subpart * 100) / Constants.BT_IMAGE_TOTAL_SUBPART)
                        subpart+=1
                        retry = 0
                else:
                    retry+=1
                    log("Unexpected reply to block {} of {} ({}); resending.".format(subpart, Constants.BT_IMAGE_TOTAL_SUBPART, readBuffer[:40].hex(" ")))
            else:
                retry+=1
                log("No reply to block {} of {}; resending.".format(subpart, Constants.BT_IMAGE_TOTAL_SUBPART))
        else:
            log("Device is not connected (block {} of {}).".format(subpart, Constants.BT_IMAGE_TOTAL_SUBPART))
            return False


def UpdateSilabImage(handle, stream, log=print, progress=PrintProgress, tick=None):
    if len(stream) != Constants.SILAB_IMAGE_SIZE:
        log("Incorrect image file size.")
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
            else:
                subpartBuffer = stream[0:]
                stream = stream[0:]
        elif retry > MAX_RETRY:
            log("No valid reply from the reader for block {} after {} retries.".format(subpart, MAX_RETRY))
            return False

        if len(subpartBuffer) > 0:
            command = SLCommands.SendImageData(subpartBuffer, subpart)
        else:
            log("Not enough image data.")
            return False

        lastBlock = (subpart == Constants.SILAB_IMAGE_TOTAL_SUBPART)

        if not USBSocket.TransmitData(handle, command):
            if lastBlock and retry > 0:
                return _SilabRestartedAfterLastBlock(log, progress, tick)
            log("Device failed to transmit data (block {} of {}).".format(subpart, Constants.SILAB_IMAGE_TOTAL_SUBPART))
            return False

        if HID.IsOpen(handle):
            readBuffer = bytes(128)
            status, readBuffer = _ReceiveReply(handle, (0xB0, 0x01), 1000)
            if status:
                if (readBuffer[0] == Constants.PREFIX) and (len(readBuffer) >= 11) and (readBuffer[8] == 0xB0) and (readBuffer[9] == 0x01):
                    if readBuffer[10] == 1:
                        log("The reader reported a network processor upgrade failure at block {}.".format(subpart))
                        return False
                    elif readBuffer[10] == 2:
                        progress(100.0)
                        log("Upload complete.")
                        utils.WaitForSeconds(SILAB_RESTART_WAIT, tick)
                        log("")
                        return True
                    else:
                        progress((subpart * 100) / Constants.SILAB_IMAGE_TOTAL_SUBPART)
                        subpart+=1
                        retry = 0
                else:
                    retry+=1
                    log("Unexpected reply to block {} of {} ({}); resending.".format(subpart, Constants.SILAB_IMAGE_TOTAL_SUBPART, readBuffer[:40].hex(" ")))
            else:
                retry+=1
                log("No reply to block {} of {}; resending.".format(subpart, Constants.SILAB_IMAGE_TOTAL_SUBPART))
        elif lastBlock:
            return _SilabRestartedAfterLastBlock(log, progress, tick)
        else:
            log("Device is not connected (block {} of {}).".format(subpart, Constants.SILAB_IMAGE_TOTAL_SUBPART))
            return False


def _SilabRestartedAfterLastBlock(log, progress, tick):
    # The network processor is also the USB bridge: once it has the last block it
    # restarts, sometimes before its "complete" reply reaches the host. Treat it as
    # done only if the reader comes back and the network processor reports a version.
    log("The reader restarted before confirming the last block; checking it after the restart...")
    progress(100.0)
    utils.WaitForSeconds(SILAB_RESTART_WAIT, tick)
    log("")
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if HID.GetNumHidDevices() > 0:
            handle = HID.Open(0)
            if handle is not None:
                slVersion = GetSLVersion(handle, log=lambda message: None)
                HID.Close(handle)
                if slVersion:
                    log("Upload complete. Network processor firmware version: {}".format(slVersion))
                    return True
        time.sleep(1)
    log("The reader did not come back after the network processor upgrade.")
    return False


class RfidPacket:
    def __init__(self, header, data):
        self.ver = header[0]
        self.flags = header[1]
        self.type = header[2] | (header[3] << 8)
        self.length = header[4] | (header[5] << 8)
        self.reserve = header[6] | (header[7] << 8)
        self.data = data


class RfidReceiver:
    # Reassembles CS108 packets from USB reads, unwraps the RFID byte stream
    # carried in 0x8100 events and splits it into RFID packets

    def __init__(self, handle):
        self.handle = handle
        self.usbBuffer = bytearray()
        self.rfidBuffer = bytearray()
        self.packets = []
        self.sendFailures = 0
        self.powerOnStatus = None

    def Pump(self):
        if not HID.IsOpen(self.handle):
            return False
        status, data = HID.ReceiveData(self.handle, HID.GetMaxReportRequest(self.handle) * HID.SIZE_MAX_READ)
        if not status:
            return False
        self.Feed(data)
        return True

    def Feed(self, data):
        self.usbBuffer += data
        while len(self.usbBuffer) >= 8:
            if self.usbBuffer[0] != Constants.PREFIX:
                # resync on the next prefix byte
                del self.usbBuffer[0]
                continue
            total = self.usbBuffer[2] + 8
            if len(self.usbBuffer) < total:
                break
            self._HandleFrame(bytes(self.usbBuffer[:total]))
            del self.usbBuffer[:total]

        while len(self.rfidBuffer) >= 8:
            ver = self.rfidBuffer[0]
            flags = self.rfidBuffer[1]
            # Command/NV-update packets carry len*4 data bytes; register and
            # control responses are header only (their len field holds data)
            if ver in (0x01, 0x02, 0x03) or (ver == 0x0D and flags == 0xF0):
                dataLen = (self.rfidBuffer[4] | (self.rfidBuffer[5] << 8)) * 4
            else:
                dataLen = 0
            if len(self.rfidBuffer) < 8 + dataLen:
                break
            self.packets.append(RfidPacket(bytes(self.rfidBuffer[:8]), bytes(self.rfidBuffer[8:8 + dataLen])))
            del self.rfidBuffer[:8 + dataLen]

    def _HandleFrame(self, frame):
        if frame[3] != Constants.TYPE_RFID or len(frame) < 10:
            return
        event = (frame[8] << 8) | frame[9]
        if event == 0x8000 and len(frame) > 10:
            self.powerOnStatus = frame[10]
        elif event == 0x8002 and len(frame) > 10 and frame[10] != 0x00:
            self.sendFailures += 1
        elif event == 0x8100:
            self.rfidBuffer += frame[10:]

    def Take(self, match, timeout):
        # Return the first received RFID packet matching match(packet), or None on timeout
        deadline = time.monotonic() + timeout / 1000
        while True:
            for i, packet in enumerate(self.packets):
                if match(packet):
                    del self.packets[i]
                    return packet
            if time.monotonic() > deadline:
                return None
            if not self.Pump():
                return None
            time.sleep(Constants.TIMER_READ * 0.001)

    def Drain(self, duration):
        # Read and discard everything that arrives within duration (ms)
        deadline = time.monotonic() + duration / 1000
        while time.monotonic() < deadline:
            self.Pump()
            time.sleep(Constants.TIMER_READ * 0.001)
        self.packets = []


def _SendRfid(handle, packets):
    for packet in packets:
        if not USBSocket.TransmitData(handle, packet):
            return False
    return True

def _RfidPowerOn(handle, receiver):
    if not USBSocket.TransmitData(handle, RFIDCommands.PowerOn(True)):
        return False
    deadline = time.monotonic() + 2
    while receiver.powerOnStatus is None and time.monotonic() < deadline:
        if not receiver.Pump():
            return False
        time.sleep(Constants.TIMER_READ * 0.001)
    receiver.Drain(500)
    return True

def _IsVersionReply(packet):
    return packet.ver in (0x70, 0x00) and packet.flags == 0x00 and packet.type == 0x0000

def _IsNVStatus(packet):
    return packet.ver == 0x0D and packet.flags == 0xF0 and packet.type == 0x0000 and len(packet.data) >= 8

def _NVStatusOf(packet):
    # NV status data: command being answered (LE32), then status (LE32)
    return int.from_bytes(packet.data[4:8], "little")

def _ReadRfidVersion(handle, receiver):
    if not _SendRfid(handle, RFIDCommands.GetVersion()):
        return ""
    packet = receiver.Take(_IsVersionReply, 2000)
    if packet is None:
        return ""
    data = (packet.reserve << 16) | packet.length
    return "{}.{}.{}".format(data >> 24, (data >> 12) & 0x7FF, data & 0x7FF)

def _ResetRfid(handle, oemValue):
    # Select bootloader (0x00000020) or main image (0x80000020), then reset
    if not _SendRfid(handle, RFIDCommands.WriteOEM(0x3C4, oemValue)):
        return False
    time.sleep(0.01)
    if not _SendRfid(handle, RFIDCommands.ReadOEM(0x3C4)):
        return False
    time.sleep(0.2)
    if not _SendRfid(handle, RFIDCommands.Reset()):
        return False
    time.sleep(2)
    return True

def GetRFIDVersion(handle, log=print):
    receiver = RfidReceiver(handle)
    if not _RfidPowerOn(handle, receiver):
        log("Cannot power on the RFID module.")
        return ""
    rfidVersion = _ReadRfidVersion(handle, receiver)
    if not rfidVersion:
        log("Cannot get RFID firmware version")
    return rfidVersion

def UpdateRFIDImage(handle, stream, log=print, progress=PrintProgress, tick=None):
    if len(stream) != Constants.RFID_IMAGE_SIZE:
        log("Incorrect image file size.")
        return False

    receiver = RfidReceiver(handle)
    if not _RfidPowerOn(handle, receiver):
        log("Cannot power on the RFID module.")
        return False

    log("Switching the RFID module to its bootloader...")
    if not _ResetRfid(handle, 0x00000020):
        log("Device failed to transmit data.")
        return False
    receiver.Drain(500)

    if not _SendRfid(handle, RFIDCommands.StartNVMemUpdate()):
        log("Device failed to transmit data.")
        return False
    if receiver.Take(lambda p: p.type == 0x300B, 5000) is None or \
       receiver.Take(lambda p: p.type in (0x0001, 0x8001), 5000) is None:
        log("The RFID module did not enter firmware update mode.")
        return False

    for block in range(Constants.RFID_IMAGE_TOTAL_SUBPART):
        if not _SendRfid(handle, RFIDCommands.SendImageData(stream[block * 32:(block + 1) * 32], block)):
            log("Device failed to transmit data (block {} of {}).".format(block + 1, Constants.RFID_IMAGE_TOTAL_SUBPART))
            return False

        reply = receiver.Take(_IsNVStatus, 2000)
        # The module announces NV update mode with an ENTRY_OK status, which can
        # arrive after the first block is sent; it is not a reply to a block
        while reply is not None and _NVStatusOf(reply) == NV_STATUS.index("NVMEMUPD_STAT_ENTRY_OK"):
            reply = receiver.Take(_IsNVStatus, 2000)
        if reply is None:
            log("No reply from the RFID module for block {}.".format(block + 1))
            _SendRfid(handle, RFIDCommands.UpdateComplete())
            return False

        status = _NVStatusOf(reply)
        if status != 0:
            name = NV_STATUS[status] if status < len(NV_STATUS) else "0x{:08X}".format(status)
            log("RFID update failed at block {}: {}".format(block + 1, name))
            _SendRfid(handle, RFIDCommands.UpdateComplete())
            return False

        if receiver.sendFailures:
            log("The reader rejected data for block {}.".format(block + 1))
            return False

        progress(((block + 1) * 100) / Constants.RFID_IMAGE_TOTAL_SUBPART)

    log("Upload complete.")
    if not _SendRfid(handle, RFIDCommands.UpdateComplete()):
        log("Device failed to transmit data.")
        return False
    utils.WaitForSeconds(RFID_RESTART_WAIT, tick)
    log("")

    log("Switching the RFID module back to the main firmware...")
    receiver.Drain(200)
    if not _ResetRfid(handle, 0x80000020):
        log("Device failed to transmit data.")
        return False
    receiver.Drain(500)

    rfidVersion = _ReadRfidVersion(handle, receiver)
    if not rfidVersion:
        log("The RFID module did not report a version after the upgrade.")
        return False
    log("RFID firmware version after upgrade: {}".format(rfidVersion))
    return True
