# CS108 USB Firmware Upgrade Tool

[![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Tkinter](https://img.shields.io/badge/GUI-Tkinter-3776AB?logo=python&logoColor=white)](https://docs.python.org/3/library/tkinter.html)
[![ctypes](https://img.shields.io/badge/FFI-ctypes-3776AB?logo=python&logoColor=white)](https://docs.python.org/3/library/ctypes.html)
[![PyInstaller](https://img.shields.io/badge/Packaging-PyInstaller-2B5B84)](https://pyinstaller.org/)
[![C++](https://img.shields.io/badge/C%2B%2B-Silicon%20Labs%20HID%20library-00599C?logo=cplusplus&logoColor=white)](USBDriver/slabhiddevice)
[![libusb](https://img.shields.io/badge/libusb-1.0-4C9A2A)](https://libusb.info/)
[![Windows](https://img.shields.io/badge/Windows-11-0078D6?logo=windows&logoColor=white)](#windows-host-setup)
[![Linux](https://img.shields.io/badge/Linux-Ubuntu%20%7C%20Raspberry%20Pi%20OS-FCC624?logo=linux&logoColor=black)](#linux-host-setup)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Upgrade the firmware of a Convergence Systems (CSL) **CS108** handheld UHF RFID reader over a USB cable.

The CS108 contains three separately upgradable processors. This repository provides two ways to upgrade them:

* **One-click upgrade app (Windows):** a standalone `.exe` that upgrades all three processors in sequence and ends with a large green **UPGRADE SUCCESSFUL** or red **UPGRADE FAILED** banner. It is meant for non-technical users and needs no Python or other software on the PC.
* **Command-line tool (Windows and Linux):** `main.py` upgrades one processor per run. It is meant for engineering and service use.

## Contents

* [Upgradable components](#upgradable-components)
* [Supported hosts](#supported-hosts)
* [One-click upgrade app](#one-click-upgrade-app)
* [Building the one-click app](#building-the-one-click-app)
* [Command-line tool](#command-line-tool)
* [Windows host setup](#windows-host-setup)
* [Linux host setup](#linux-host-setup)
* [How it works](#how-it-works)
* [Troubleshooting](#troubleshooting)
* [Repository layout](#repository-layout)
* [License](#license)

## Upgradable components

| Component | Chip | Firmware file | Exact size | Folder | CLI switch |
|-----------|------|---------------|------------|--------|------------|
| Network processor (also the reader's USB bridge) | Silicon Labs C8051F380 | `*.img` (e.g. `F380_Image_V1017.img`) | 16,384 bytes | `FW\Network` | `/N` |
| Bluetooth processor | TI CC2541 | `*.bin` (e.g. `CS108_CC2541_APP_V1020.bin`) | 124,928 bytes | `FW\Bluetooth` | `/B` |
| RFID module | CSL RFID module | `image_*.a79` (e.g. `image_V2646.a79`) | 203,776 bytes | `FW\RFID` | `/R` |

The repository ships with Network 1.0.17, Bluetooth 1.0.20 and RFID 2.6.46 images. Only main firmware images are supported; bootloader images are not.

## Supported hosts

| Host | Python runtime | Status |
|------|----------------|--------|
| Windows 11, x64 | Python 3.14, **32-bit** | Tested, including the packaged one-click app |
| Ubuntu 20.04 LTS, x64 | Python 3 | Command-line tool tested with an earlier release; not yet re-tested with the RFID upgrade and recent changes |
| Raspberry Pi 4 (Raspbian), arm32 | Python 3 | Command-line tool tested with an earlier release; not yet re-tested with the RFID upgrade and recent changes |
| macOS | | Not tested; `HID.py` only loads `SLABHIDDevice.dll` (Windows) or `libslabhiddevice.so` |

The Python code uses only the standard library (`ctypes`, `tkinter`). The USB communication goes through the Silicon Labs HID library: a prebuilt 32-bit DLL on Windows, or `libslabhiddevice.so` built from the vendored source on Linux.

## One-click upgrade app

### Using it

1. Connect the CS108 to the PC with the USB cable and power the reader on.
2. Double-click `CS108FirmwareUpgrade.exe` (or run `OneClickUpgrade.py` with 32-bit Python).
3. Wait. Do not unplug the reader while the amber **UPGRADING — DO NOT UNPLUG** banner is shown.
4. Read the result:
   * Green **UPGRADE SUCCESSFUL**: all three processors were upgraded. The installed versions are shown below the banner.
   * Red **UPGRADE FAILED**: the upgrade stopped. The reason is shown in red below the banner and in the log. Check the reason, fix it (see [Troubleshooting](#troubleshooting)) and run the app again.
5. Click **Close**.

A full run takes about 3 minutes.

### What it does

1. **Checks the firmware files** before touching the reader. Each of `FW\Network`, `FW\Bluetooth` and `FW\RFID` must contain exactly one firmware file of the exact expected size. If not, it stops straight away and nothing is sent to the reader.
2. **Detects and connects** to the first CS108 found on USB.
3. **Upgrades the Network processor (step 1 of 3)**, showing the current version, the file, a progress bar and a 5-second restart countdown.
4. **Reconnects** to the reader, which restarts and reappears on USB.
5. **Upgrades the Bluetooth processor (step 2 of 3)**, with a 15-second restart countdown.
6. **Reconnects** again.
7. **Upgrades the RFID module (step 3 of 3)**, which includes a 6-second restart.
8. **Reads back all three versions** and shows them under the green banner.

If any step fails, the workflow stops immediately and reports the failure. The app always reinstalls all three images, even when the reader already runs those versions.

If a processor's current version cannot be read, for example because an earlier interrupted upgrade left it in its bootloader, the app shows "unknown" and continues with the upgrade. Running the app again is therefore the way to recover a reader after a failed upgrade.

Closing the window during an upgrade asks for confirmation, because interrupting an upgrade can leave the reader unusable until it is upgraded again.

### Log file

Every message shown in the app's log pane is also appended, with a timestamp, to `CS108FirmwareUpgrade.log` in the same folder as the exe. If that folder is not writable, the upgrade still runs; only the file is skipped.

### Changing the firmware to install

Replace the file in the matching `FW` subfolder, keeping exactly one file per folder. No rebuild is needed: the app reads the `FW` folder next to the exe every time it starts.

## Building the one-click app

Run on a Windows PC with 32-bit Python 3.14 installed (see [Windows host setup](#windows-host-setup)):

```
> build_exe.bat
```

The script:

1. Stops with a message if a previous `dist\CS108FirmwareUpgrade\CS108FirmwareUpgrade.exe` is still running. It deletes and recreates that folder, so close the app first.
2. Installs or updates PyInstaller in the 32-bit Python.
3. Builds a single-file, windowed `CS108FirmwareUpgrade.exe` with `SLABHIDDevice.dll` and the Python runtime embedded.
4. Assembles the distributable folder:

```
dist\CS108FirmwareUpgrade\
├── CS108FirmwareUpgrade.exe
└── FW\
    ├── Network\F380_Image_V1017.img
    ├── Bluetooth\CS108_CC2541_APP_V1020.bin
    └── RFID\image_V2646.a79
```

Copy the whole `dist\CS108FirmwareUpgrade` folder to the target PC, for example on a USB stick or as a zip file, and double-click the exe. Put it in a folder the user can write to, such as the Desktop or Documents, so the log file can be created. The exe is not code-signed, so Windows SmartScreen may show "Windows protected your PC" on first launch. Choose **More info**, then **Run anyway**.

## Command-line tool

`main.py` upgrades one processor per run:

```
Usage: python main.py [ /B | /N | /R ] file
```

| Switch | Upgrades |
|--------|----------|
| `/N` | Network processor (Silicon Labs) |
| `/B` | Bluetooth processor |
| `/R` | RFID module |

On Windows, replace `python` with your 32-bit runtime (`py -V:3.14-32` or `python3.14-32`; see [Windows host setup](#windows-host-setup)).

Example:

```
$ python main.py /B ./FW/Bluetooth/CS108_CC2541_APP_V1020.bin
----------------------------
CS108 Firmware Upgrade Toool
----------------------------
Number of USB device(s) connected:  1
Device 0: \\?\hid#vid_10c4&pid_8468#...
Open the first device found...
Device opened: handle=60622816
Current Bluetooth firmware version: 1.0.17
Upgrade Bluetooth firmware with file: ./FW/Bluetooth/CS108_CC2541_APP_V1020.bin
Completed: 100.0%
Upload complete.
>> Wait for 0 seconds
Bluetooth firmware upgrade successful
```

`python HID.py` is a smoke test for the USB layer: it lists the connected readers, opens the first one, sends a Bluetooth version query and closes the reader again. It reads the reply only once without waiting, so "Received Data" is usually empty.

## Windows host setup

No build step and no driver installation are needed. Windows talks to the reader with its built-in USB HID driver, and the scripts load the prebuilt Silicon Labs library `USBDriver\SLABHIDDevice.dll`.

**The DLL is 32-bit, so the Python scripts must run on a 32-bit Python runtime.** A 64-bit Python cannot load a 32-bit DLL and stops with:

```
OSError: Unable to load ...\USBDriver\SLABHIDDevice.dll: the DLL is 32-bit, run with 32-bit Python
```

Many PCs have only 64-bit Python installed, and the plain `python` command usually starts it. Set up a 32-bit runtime as follows:

* Install 32-bit Python 3.14, either with the Python install manager:

```
> py install 3.14-32
```

  or with the **Windows installer (32-bit)** from [python.org](https://www.python.org/downloads/windows/).

* Check that the runtime is 32-bit (it should print `32`):

```
> py -V:3.14-32 -c "import struct; print(struct.calcsize('P') * 8)"
```

* Run the scripts with that runtime, by naming it explicitly:

```
> py -V:3.14-32 main.py /B .\FW\Bluetooth\CS108_CC2541_APP_V1020.bin
```

  or with the `python3.14-32` command that the install manager adds:

```
> python3.14-32 main.py /B .\FW\Bluetooth\CS108_CC2541_APP_V1020.bin
```

* Optionally, make 32-bit Python the default so that plain `py` and `python` use it. This affects every Python program you run, so only do it if that suits you. Open a new terminal afterwards:

```
> setx PYTHON_MANAGER_DEFAULT 3.14-32
```

The packaged one-click app contains its own 32-bit Python, so its users do not need any of this.

## Linux host setup

On Linux the scripts use `libslabhiddevice.so`, the Silicon Labs HID library built on libusb. Build it from the source in `USBDriver/slabhiddevice` (Ubuntu/Debian commands shown):

1. Install the build dependencies:

```
$ sudo apt-get install g++
$ sudo apt-get install autoconf
$ sudo apt-get install libtool
$ sudo apt-get install libudev-dev
```

2. Install libusb 1.0.23 or later. The version in the package repository may be outdated, so we suggest building the latest [libusb release](https://github.com/libusb/libusb/releases) from source. In the extracted package, run:

```
$ ./autogen.sh
$ ./configure
$ make
$ sudo make install
```

3. Build and install `libslabhiddevice.so` to `/usr/local/lib`, where the Python code loads it from:

```
$ cd USBDriver/slabhiddevice
$ make
$ sudo make install
```

4. Copy `USBDriver/slabhiddevice/doc/SiliconLabs.rules` to `/etc/udev/rules.d/`, then unplug and replug the reader. This gives non-root users read/write access to the reader through libusb.

## How it works

### Software layers

```
OneClickUpgrade.py (Tkinter GUI)   main.py (command line)
                 \                  /
          CS108FwUpgrade.py   version queries and upgrade procedures
                       |
  BTCommands.py / SLCommands.py / RFIDCommands.py   packet builders
                       |
          USBSocket.py   transmit / receive with timeouts
                       |
          HID.py   ctypes binding, 61-byte HID report framing
                       |
  SLABHIDDevice.dll (Windows) / libslabhiddevice.so (Linux)
                       |
           CS108 USB HID bridge (VID 0x10C4, PID 0x8468)
```

The GUI runs the upgrade on a worker thread and updates the window from a message queue, so the window stays responsive during long transfers.

### CS108 packets

Every command and reply is a CS108 packet: an 8-byte header followed by a payload.

| Byte | Meaning |
|------|---------|
| 0 | Prefix `0xA7` |
| 1 | Connection: `0xE6` USB, `0xB3` Bluetooth |
| 2 | Payload length |
| 3 | Module: `0xE8` network processor, `0x5F` Bluetooth, `0xC2` RFID, `0xD9` notification |
| 4 | Reserved `0x82` |
| 5 | Direction: `0x37` host to reader, `0x9E` reader to host |
| 6–7 | CRC-16 (0 when sent by the host) |

The payload starts with a 2-byte command code: `0xB0xx` network processor, `0xC0xx` Bluetooth, `0x80xx` RFID. `xx00` reads the version, and `xx01` sends one block of a firmware image.

### Network and Bluetooth upgrades

The image is sent in numbered blocks: 144 blocks of 114 bytes for the network processor, and 1,952 blocks of 64 bytes for Bluetooth. The reader answers each block with "continue", "failed" or "complete". After "complete" the processor restarts, and the tool waits 5 s (network) or 15 s (Bluetooth).

### RFID upgrade

The RFID upgrade follows the procedure of CSL's CS108 PC Demo App:

1. Power on the RFID module and read its version.
2. Restart it into its bootloader.
3. Enter firmware update mode.
4. Send 6,368 blocks of 32 bytes, each protected by a CRC-32 and acknowledged individually.
5. Finish the update and wait 6 s.
6. Restart into the new firmware and read the new version.

If an RFID upgrade is interrupted, the module stays in its bootloader; running the upgrade again completes it.

### Reliability measures

* **Pre-flight checks:** firmware file presence, count and exact size are checked before anything is sent.
* **Notifications are ignored:** the reader sends unsolicited notification packets during transfers, sometimes in the same USB read as a reply. They are skipped rather than mistaken for a bad reply, so blocks are not resent needlessly.
* **Bounded retries:** a block without a reply is resent up to 10 times, then the upgrade fails instead of hanging.
* **Network processor restart:** the network processor is also the USB bridge, and on some PCs it restarts before its final "complete" reply arrives. In that case the tool waits for the reader to reappear and confirms that the network processor reports a version.
* **Reconnect between steps:** the reader re-enumerates on USB after restarts, so the one-click app closes and reopens it before each step, waiting up to 30 s.
* **Verification:** the one-click app reads back all three versions at the end.

## Troubleshooting

| Message | Cause | What to do |
|---------|-------|------------|
| No CS108 reader detected | Reader not connected, not powered on, or not recognised over USB | Check the cable, power the reader on, try another USB port, then run again |
| No … firmware file found / More than one … firmware file found / … has the wrong size | The `FW` folder next to the exe is missing a file, has extra files, or contains the wrong kind of image | Put exactly one correct image in each of `FW\Network`, `FW\Bluetooth`, `FW\RFID` |
| Cannot load the USB driver / `OSError: ... the DLL is 32-bit` | Scripts run with 64-bit Python | Use 32-bit Python (see [Windows host setup](#windows-host-setup)), or use the packaged exe |
| Device failed to transmit data (block N of M) | The reader disconnected from USB during the transfer | Check the cable and USB port (avoid unpowered hubs), then run again |
| No valid reply from the reader for block N after 10 retries | The reader stopped answering during the transfer | Power-cycle the reader, then run again |
| RFID update failed at block N: NVMEMUPD_STAT_… | The RFID module rejected a block | Run again; the module stays in its bootloader and the next run completes the upgrade |
| The reader did not come back after the network processor upgrade | The reader did not reappear on USB within 30 s after restarting | Unplug and replug the reader, then run again |

After any failure, running the one-click app again is safe, and it is the normal way to recover. Send `CS108FirmwareUpgrade.log` to support if the problem persists.

## Repository layout

| Path | Purpose |
|------|---------|
| `OneClickUpgrade.py` | One-click Tkinter app: file checks, three-step workflow, progress display, result banner, log file |
| `main.py` | Command-line tool: one processor per run (`/N`, `/B`, `/R`) |
| `CS108FwUpgrade.py` | Version queries and upgrade procedures for the network processor, Bluetooth and RFID module |
| `BTCommands.py`, `SLCommands.py`, `RFIDCommands.py` | Build the CS108 command packets for each processor (including the RFID CRC-32) |
| `USBSocket.py` | Send and receive CS108 packets with error handling and timeouts |
| `HID.py` | `ctypes` binding to the Silicon Labs HID library; splits data into 61-byte HID reports |
| `CRC.py` | CRC-16 check for packets received from the reader |
| `Constants.py` | Packet constants, image sizes and block counts |
| `utils.py` | Countdown helper used for restart waits |
| `build_exe.bat` | Builds the standalone one-click app with PyInstaller |
| `FW/` | Firmware images, one subfolder per processor |
| `USBDriver/SLABHIDDevice.dll` | Prebuilt 32-bit Silicon Labs HID library for Windows |
| `USBDriver/slabhiddevice/` | Silicon Labs HID library source for Linux (C/C++, libusb) |

## License

Released under the [MIT License](LICENSE). Copyright (c) 2022 Convergence Systems Limited.
