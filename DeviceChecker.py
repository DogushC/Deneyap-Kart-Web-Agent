import multiprocessing
from multiprocessing import Process, Queue
from serial.tools import list_ports
import time
import logging

class DeviceChecker:
    """
    Bilgisayarlara bağlı olan kartları devamlı olarak kontrol eden sınıf, ayrı bir process açarak çalışır


    queue(Manager.Queue): Ana process'e veri göndermek için

    startStopQueue(Manager.Queue): Dışarıdan gelen veriyi almak
    """
    def __init__(self, queue):
        self.queue = queue
        self.startStopQueue = Queue()
        self.process = Process(target=self.queuer, args=(self.queue, self.startStopQueue))
        logging.info(f"Starting process for DeviceChekcer with PID:{self.process.pid}")

        self.process.start()

    def queuer(self, queue: multiprocessing.Queue, startStopQueue: multiprocessing.Queue) -> None:
        """
        Yeni kart bulunduğunda ana procces's queue aracılığı ile bildirim gönderir. Yeni kartların eklenip eklenmediğini
        while döngüsü içerisinde kontrol eder.


        queue(Manager.Queue): Ana process'e veri göndermek için

        startStopQueue(Manager.Queue): Dışarıdan gelen veriyi almak
        """
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
                    logging.info(f"Change on devices")
                    queue.put({"sender":"deviceChecker", "command":"getBoards"})

            time.sleep(1)
    def start(self) -> None:
        """
        querer fonksiyonun içerisinde ki while döngüsünün çalışmasını sağlar
        """
        self.startStopQueue.put({"command":"startDeviceChecker"})
        logging.info(f"Starting device checker")

    def stop(self) -> None:
        """
        querer fonksiyonun içerisinde ki while döngüsünün durmasını sağlar
        """
        self.startStopQueue.put({"command": "stopDeviceChecker"})
        logging.info(f"Stoping device checker")

    def terminate(self) -> None:
        """
        querer fonksiyonun içerisinde ki while döngüsünü bitirir.
        """
        self.startStopQueue.put({"command": "terminateDeviceChecker"})
        logging.info(f"Termitating device checker")

    def enumerate_serial_devices(self) -> set:
        """
        bilgisayarın portlarına takılı olan kartları çeker
        """
        return set([item for item in list_ports.comports()])

    def check_new_devices(self, old_devices: set) -> (set, bool):
        """
        eski kartlar ile yeni çekilen kartları karşılaştırarak, eklenen ya da çıkarılan kartın olup olmadığına bakar
        """
        devices = self.enumerate_serial_devices()
        added = devices.difference(old_devices)
        removed = old_devices.difference(devices)
        changed = True if added or removed else False
        return devices, changed