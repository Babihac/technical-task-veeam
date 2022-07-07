from pathlib import Path
import subprocess
import psutil
import threading
import time
import os
import csv

headers = ["CPU usage [%]", "RSS", "VMZ", "FDS"]


def init(path, interval):
    process = subprocess.Popen(path)
    p = psutil.Process(process.pid)
    watchProcess(p, interval)
   

def getProcessInfo(process):
    try:
        os.kill(process.pid, 0)
        return [process.cpu_percent(), process.memory_info().rss, process.memory_info().vms, process.num_fds()]
    except:
        print("Process with pid {} does not exist".format(process.pid))
        exit(1)

def watchProcess(process, interval):
    ticker = threading.Event()
    while True:
        data = getProcessInfo(process)
        printProcessInfo(data)
        storeProcessInfo("processWatcher.csv", data)
        time.sleep(interval)

def storeProcessInfo(filename, data):
    fileExist = os.path.isfile(filename)
    with open(filename, 'a') as csvfile:
        writer = csv.writer(csvfile)
        if not fileExist:
            writer.writerow(headers)
        writer.writerow(data)

def printProcessInfo(data):
    print("CPU usage [%] = {}".format(data[0]))
    print("RSS = {}".format(data[1]))
    print("VMZ = {}".format(data[2]))
    print("FDS = {}".format(data[3]))





