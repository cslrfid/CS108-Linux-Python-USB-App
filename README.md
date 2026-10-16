## CS108 USB Tool for Firmware Updates

This tool allows you to control your reader and perform firmware update with a Linux/Windows/MacOS host

The code is written in Python and tested on x64 desktop (Ubuntu 20.04 LTS), arm32 (Raspberry Pi 4/Raspbian) and x64 Windows (Windows 11) running a 32-bit Python runtime (Python 3.14, see [Windows Host](#windows-host)).

### Compile the HID-UART API Library on your Linux Host

This will generate the `libslabhiddevice.so` file so that the python code will be invoking this native library for communicating with the CS108.

Please look under the `USBDriver` folder and you can find the source code and instruction for building from source.

* Install dependencies (Ubuntu/Debian-based system)

```
$ sudo apt-get install g++
$ sudo apt-get install autoconf
$ sudo apt-get install libtool
$ sudo apt-get install libudev-dev
```

* You will also need libusb.  However, the version that you download from the package repository could be outdated and we suggest to install the latest version (v1.0.23 or later).  You can download the source code pakage from **[here](https://github.com/libusb/libusb/releases)**.  
Extract the package at your local and run the following commands for generating the Makefile:

```
$ ./autogen.sh
$ ./configure
```

* Run the following to build and install libusb on your machine:

```
$ make
$ make install
```

* After installing all the dependencies, build the library libslabhiddevice.so by running the following under /USBDriver/slabhiddevice: 

```
$ make 
```

* Install library to /usr/local/lib (to be referenced by the python code)

```
$ sudo make install
```

* Copy the file SiliconLabs.rules under `USBDriver/slabhiddevice/doc` to `/etc/udev/rules.d` 

This allows libusb-1.0 to have read/write access to the device

### Windows Host

No build step and no driver installation are needed: Windows talks to the reader with its built-in USB HID driver, and the scripts load the prebuilt Silicon Labs library `USBDriver\SLABHIDDevice.dll`.

**The DLL is 32-bit, so the Python scripts must run on a 32-bit Python runtime.**  A 64-bit Python cannot load a 32-bit DLL and stops with:

```
OSError: Unable to load ...\USBDriver\SLABHIDDevice.dll: the DLL is 32-bit, run with 32-bit Python
```

Many PCs have only 64-bit Python installed, and the plain `python` command usually starts it.  Set up a 32-bit runtime as follows:

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

* Optionally, make 32-bit Python the default so that plain `py` and `python` use it.  This affects every Python program you run, so only do it if that suits you.  Open a new terminal afterwards:

```
> setx PYTHON_MANAGER_DEFAULT 3.14-32
```

The standalone one-click app described below already contains its own 32-bit Python, so users of the packaged exe do not need any of this.

### One-Click Firmware Upgrade (Windows)

`OneClickUpgrade.py` upgrades all three processors in one go, with no questions asked:

1. Network processor, using the single `*.img` file in `FW\Network`
2. Bluetooth processor, using the single `*.bin` file in `FW\Bluetooth`
3. RFID processor, using the single `image_*.a79` file in `FW\RFID`

Connect the reader by USB and power it on, then start the tool.  It shows each step's current version, file and progress, and finishes with a large green **UPGRADE SUCCESSFUL** or red **UPGRADE FAILED** banner.  It stops at the first failure.

To update the firmware being installed, replace the file in the matching `FW` subfolder (keep exactly one file per folder).

#### Building the standalone app

Run `build_exe.bat` on a Windows PC with 32-bit Python 3.14 installed.  It installs PyInstaller and creates `dist\CS108FirmwareUpgrade\`, containing `CS108FirmwareUpgrade.exe` and the `FW` folders.  Copy that whole folder to any Windows PC and double-click the exe: no Python or other software needs to be installed there.

### Running the Python Scripts

Run the main.py with the firmware file as the argument:

* /B: Bluetooth Firmware
* /N: Network Processor Firmware
* /R: RFID Firmware

```
Usage: python main.py [ /B | /N | /R ] file
```	

On Windows, replace `python` with your 32-bit runtime (`py -V:3.14-32` or `python3.14-32`; see [Windows Host](#windows-host)).

Example
```
$ python main.py /B ./FW/Bluetooth/CS108_CC2541_APP_V1020.bin 
----------------------------
CS108 Firmware Upgrade Toool
----------------------------
Number of USB device(s) connected:  1
Device 0: 0001:006a:00
Open the first device found...
Device opened: handle=26675736
Current Bluetooth firmware version: 1.0.17
Upgrade Bluetooth firmware with file: ./FW/Bluetooth/CS108_CC2541_APP_V1020.bin
Completed: 100.0%
Upload complete.
>> Wait for 0 secondss
Bluetooth firmware upgrade successful
```


