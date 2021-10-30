from multiprocessing import Process, Queue
from serial.tools import list_ports
import time
import logging

class DeviceChecker:

    def __init__(self, queue):
        self.queue = queue
        self.startStopQueue = Queue()
        process = Process(target=self.queuer, args=(self.queue, self.startStopQueue))
        logging.info(f"Starting process for DeviceChekcer with PID:{process.pid}")

        process.start()

    def queuer(self, queue, startStopQueue):
        logging.info(f"Process Started Succesfully")
        runner = False
        old_devices = self.enumerate_serial_devices()

        while True:
            if not startStopQueue.empty():
                command = startStopQueue.get()['command']
                if command == 'startDeviceChecker':
                    logging.info(f"Device checker Started")
                    runner = True
                elif command == 'stopDeviceChecker':
                    logging.info(f"Device checker Stoped")
                    runner = False
                elif command == 'terminateDeviceChecker':
                    logging.info(f"Device checker Terminated")
                    break

            if runner:
                old_devices, changed = self.check_new_devices(old_devices)
                if changed:
                    logging.info(f"Found new device")
                    queue.put({"sender":"deviceChecker", "command":"getBoards"})

            time.sleep(1)

    def start(self):
        self.startStopQueue.put({"command":"startDeviceChecker"})
        logging.info(f"Starting device checker")

    def stop(self):
        self.startStopQueue.put({"command": "stopDeviceChecker"})
        logging.info(f"Stoping device checker")

    def terminate(self):
        self.startStopQueue.put({"command": "terminateDeviceChecker"})
        logging.info(f"Termitating device checker")

    def enumerate_serial_devices(self):
        return set([item for item in list_ports.comports()])

    def check_new_devices(self, old_devices):
        devices = self.enumerate_serial_devices()
        added = devices.difference(old_devices)
        removed = old_devices.difference(devices)
        changed = True if added or removed else False
        return devices, changed