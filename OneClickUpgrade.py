import glob
import os
import queue
import sys
import threading
import time
import traceback
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

import Constants

TITLE = "CS108 Firmware Upgrade"

# Upgrade order: (step name, FW subfolder, file pattern, expected size)
STEPS = [
    ("Network processor", "Network", "*.img", Constants.SILAB_IMAGE_SIZE),
    ("Bluetooth processor", "Bluetooth", "*.bin", Constants.BT_IMAGE_SIZE),
    ("RFID processor", "RFID", "image_*.a79", Constants.RFID_IMAGE_SIZE),
]

RECONNECT_TIMEOUT = 30 # seconds to wait for the reader to come back on USB
LOG_FILE = "CS108FirmwareUpgrade.log" # appended next to the exe

COLOR_RUNNING = "#F2A900"
COLOR_SUCCESS = "#1E8E3E"
COLOR_FAILURE = "#C5221F"


class UpgradeError(Exception):
    pass


def BaseFolder():
    # Folder holding the FW directory: next to the exe when packaged, else next to this script
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def FindFirmwareFiles():
    files = []
    for name, folder, pattern, size in STEPS:
        path = os.path.join(BaseFolder(), "FW", folder)
        matches = sorted(glob.glob(os.path.join(path, pattern)))
        if len(matches) == 0:
            raise UpgradeError("No {} firmware file ({}) found in:\n{}".format(name, pattern, path))
        if len(matches) > 1:
            raise UpgradeError("More than one {} firmware file found in:\n{}\nKeep only one.".format(name, path))
        if os.path.getsize(matches[0]) != size:
            raise UpgradeError("{} firmware file has the wrong size ({} bytes, expected {}):\n{}".format(
                name, os.path.getsize(matches[0]), size, matches[0]))
        files.append(matches[0])
    return files


class Workflow:
    # Runs on a worker thread; reports to the UI only through the event queue

    def __init__(self, events):
        self.events = events
        self.lastMessage = ""

    def Post(self, kind, *args):
        self.events.put((kind,) + args)

    def Log(self, message):
        message = message.strip()
        if message:
            self.lastMessage = message
            self.Post("log", message)
            try:
                with open(os.path.join(BaseFolder(), LOG_FILE), "a", encoding="utf-8") as f:
                    f.write("{} {}\n".format(time.strftime("%Y-%m-%d %H:%M:%S"), message))
            except OSError:
                pass # the on-screen log still has it

    def Run(self):
        try:
            versions = self.Upgrade()
            self.Post("done", True, "Network {}   ·   Bluetooth {}   ·   RFID {}".format(*versions))
        except UpgradeError as e:
            self.Log(str(e))
            self.Post("done", False, str(e))
        except Exception as e:
            self.Log(traceback.format_exc())
            self.Post("done", False, "Unexpected error: {}".format(e))

    def Upgrade(self):
        self.Log("==== {} started ====".format(TITLE))
        files = FindFirmwareFiles()

        try:
            import HID
            import CS108FwUpgrade
        except OSError as e:
            raise UpgradeError("Cannot load the USB driver: {}".format(e))
        self.HID = HID

        self.Post("step", "Detecting reader", "", "")
        handle = self.Connect(0)

        upgrades = [
            (CS108FwUpgrade.GetSLVersion, CS108FwUpgrade.UpdateSilabImage),
            (CS108FwUpgrade.GetBTVersion, CS108FwUpgrade.UpdateBTImage),
            (CS108FwUpgrade.GetRFIDVersion, CS108FwUpgrade.UpdateRFIDImage),
        ]

        try:
            for index, ((name, _, _, _), fileName, (getVersion, update)) in enumerate(zip(STEPS, files, upgrades)):
                if index > 0:
                    handle = self.Reconnect(handle)

                title = "Step {} of 3: {}".format(index + 1, name)
                self.Post("step", title, "", os.path.basename(fileName))
                self.Log("---- {} ----".format(title))

                version = getVersion(handle, log=self.Log)
                if not version:
                    # e.g. left in its bootloader by an interrupted upgrade; the upgrade itself can recover it
                    self.Log("Cannot read the current version; continuing with the upgrade.")
                    version = "unknown"
                self.Post("step", title, version, os.path.basename(fileName))
                self.Log("Current version: {}".format(version))
                self.Log("Upgrading with file: {}".format(fileName))

                with open(fileName, "rb") as f:
                    stream = f.read()

                self.Post("progress", 0.0)
                if not update(handle, stream, log=self.Log, progress=self.Progress, tick=self.Tick):
                    raise UpgradeError("{} upgrade failed.\n{}".format(name, self.lastMessage))
                self.Log("{} upgrade successful.".format(name))

            # Read back what the reader now runs
            handle = self.Reconnect(handle)
            self.Post("step", "Checking new firmware versions", "", "")
            versions = [CS108FwUpgrade.GetSLVersion(handle, log=self.Log),
                        CS108FwUpgrade.GetBTVersion(handle, log=self.Log),
                        CS108FwUpgrade.GetRFIDVersion(handle, log=self.Log)]
            self.Log("New versions: Network {}, Bluetooth {}, RFID {}".format(*versions))
            if not all(versions):
                raise UpgradeError("Cannot read back the firmware versions after the upgrade.")
            return versions
        finally:
            HID.Close(handle)

    def Progress(self, percent):
        self.Post("progress", percent)

    def Tick(self, secondsLeft):
        self.Post("wait", secondsLeft)

    def Connect(self, settleSeconds):
        HID = self.HID
        deadline = time.monotonic() + max(settleSeconds, 1)
        while True:
            if HID.GetNumHidDevices() > 0:
                handle = HID.Open(0)
                if handle is not None:
                    self.Log("Reader connected: {}".format(HID.GetHidString(0)))
                    return handle
            if time.monotonic() > deadline:
                break
            time.sleep(1)
        raise UpgradeError("No CS108 reader detected.\nConnect the reader with the USB cable, power it on and try again.")

    def Reconnect(self, handle):
        # The reader may restart and re-enumerate on USB after an upgrade
        self.HID.Close(handle)
        time.sleep(1)
        self.Log("Reconnecting to the reader...")
        return self.Connect(RECONNECT_TIMEOUT)


class App:
    def __init__(self, root):
        self.root = root
        self.events = queue.Queue()
        self.running = True

        # Fonts are in points and follow the display scaling; scale the pixel sizes to match
        scale = root.winfo_fpixels("1i") / 96
        root.title(TITLE)
        root.geometry("{}x{}".format(int(840 * scale), int(680 * scale)))
        root.minsize(int(760 * scale), int(600 * scale))
        root.protocol("WM_DELETE_WINDOW", self.OnClose)

        self.banner = tk.Label(root, text="UPGRADING — DO NOT UNPLUG", font=("Segoe UI", 30, "bold"),
                               bg=COLOR_RUNNING, fg="white", pady=18)
        self.banner.pack(fill="x")

        self.closeButton = tk.Button(root, text="Close", font=("Segoe UI", 12), width=12, state="disabled",
                                     command=root.destroy)
        self.closeButton.pack(side="bottom", pady=(0, 12))

        self.detail = tk.Label(root, text="", font=("Segoe UI", 13, "bold"), wraplength=int(800 * scale),
                               justify="center")
        self.detail.pack(fill="x", padx=16, pady=(8, 0))

        info = tk.Frame(root)
        info.pack(fill="x", padx=16, pady=8)
        self.stepLabel = tk.Label(info, text="Checking firmware files...", font=("Segoe UI", 16, "bold"), anchor="w")
        self.stepLabel.pack(fill="x")
        self.versionLabel = tk.Label(info, text="", font=("Segoe UI", 12), anchor="w")
        self.versionLabel.pack(fill="x")
        self.fileLabel = tk.Label(info, text="", font=("Segoe UI", 12), anchor="w")
        self.fileLabel.pack(fill="x")

        bar = tk.Frame(root)
        bar.pack(fill="x", padx=16)
        self.progress = ttk.Progressbar(bar, maximum=100)
        self.progress.pack(side="left", fill="x", expand=True)
        self.percentLabel = tk.Label(bar, text="0%", width=6, font=("Segoe UI", 12, "bold"))
        self.percentLabel.pack(side="left", padx=(8, 0))
        self.waitLabel = tk.Label(root, text="", font=("Segoe UI", 12), anchor="w")
        self.waitLabel.pack(fill="x", padx=16, pady=(4, 0))

        self.log = scrolledtext.ScrolledText(root, height=10, font=("Consolas", 10), state="disabled")
        self.log.pack(fill="both", expand=True, padx=16, pady=8)

        threading.Thread(target=Workflow(self.events).Run, daemon=True).start()
        root.after(50, self.Poll)

    def Poll(self):
        while True:
            try:
                event = self.events.get_nowait()
            except queue.Empty:
                break
            getattr(self, "On" + event[0].capitalize())(*event[1:])
        if self.running:
            self.root.after(50, self.Poll)

    def OnLog(self, message):
        self.log.configure(state="normal")
        self.log.insert("end", message + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def OnStep(self, title, version, fileName):
        self.stepLabel.config(text=title)
        self.versionLabel.config(text="Current version: {}".format(version) if version else "")
        self.fileLabel.config(text="File: {}".format(fileName) if fileName else "")
        self.waitLabel.config(text="")

    def OnProgress(self, percent):
        self.progress["value"] = percent
        self.percentLabel.config(text="{:.0f}%".format(percent))
        self.waitLabel.config(text="")

    def OnWait(self, secondsLeft):
        self.waitLabel.config(text="Restarting... please wait {} s".format(secondsLeft))

    def OnDone(self, success, message):
        self.running = False
        if success:
            self.banner.config(text="✔  UPGRADE SUCCESSFUL", bg=COLOR_SUCCESS, font=("Segoe UI", 44, "bold"))
            self.detail.config(text=message, fg=COLOR_SUCCESS)
            self.stepLabel.config(text="All 3 firmware upgrades completed.")
        else:
            self.banner.config(text="✘  UPGRADE FAILED", bg=COLOR_FAILURE, font=("Segoe UI", 44, "bold"))
            self.detail.config(text=message, fg=COLOR_FAILURE)
        self.waitLabel.config(text="")
        self.closeButton.config(state="normal")

    def OnClose(self):
        if not self.running:
            self.root.destroy()
            return
        if messagebox.askyesno(TITLE, "A firmware upgrade is in progress.\n\n"
                               "Closing now can leave the reader unusable.\n\nClose anyway?",
                               icon="warning", default="no"):
            os._exit(1)


def main():
    try:
        # Sharp text on high-DPI screens
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    root = tk.Tk()
    App(root)
    root.mainloop()

if __name__ == '__main__':
    main()
