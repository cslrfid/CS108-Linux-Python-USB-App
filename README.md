## CS108 USB Tool for Firmware Updates

This tool allows you to control your reader and perform firmware update with a Linux/Windows/MacOS host

The code is written in Python and tested on x64 desktop (Ubuntu 20.04 LTS) and arm32 (Raspberry Pi 4/Raspbian).

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

### Running the Python Scripts

Run the main.py with the firmware file as the argument:

* /B: Bluetooth Firmware
* /N: Network Processor Firmware
* /R: RFID Firmware

```
Usage: python main.py [ /B | /N | /R ] file
```	

####Example
```
$ python main.py /B ./FW/CS108_CC2541_APP_V1017.bin 
----------------------------
CS108 Firmware Upgrade Toool
----------------------------
Number of USB device(s) connected:  1
Device 0: 0001:006a:00
Open the first device found...
Device opened: handle=26675736
Current Bluetooth firmware version: 1.0.17
Upgrade Bluetooth firmware with file: ./FW/CS108_CC2541_APP_V1017.bin
Completed:100.0%
>> Wait for 0 secondss
Bluetooth firmware upgrade successful
```


