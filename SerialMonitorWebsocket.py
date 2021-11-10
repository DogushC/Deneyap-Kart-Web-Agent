import asyncio
import json
import traceback
from utils import Data
import serial
import logging
import config

class aobject(object):
    """Inheriting this class allows you to define an async __init__.

    So you can create objects by doing something like `await MyClass(params)`
    """
    async def __new__(cls, *a, **kw):
        instance = super().__new__(cls)
        await instance.__init__(*a, **kw)
        return instance

    async def __init__(self):
        pass


class SerialMonitorWebsocket(aobject):
    """
    Serial monitorün çalıştığı sınıf, her bir websocket bağlantısı için bir SerialMonitorWebsocket objesi oluşturulur.


    websocket(websocket): web tarafı ile yapılan socket bağlantısının objesi

    path(str):
    """
    async def __init__(self, websocket, path):
        logging.info(f"SerialMonitorWebsocket is object created")

        self.websocket = websocket
        self.serialOpen = False
        self.ser = None
        await self.mainLoop()

    async def commandParser(self, body):
        """
        web tarfından gelen bilgiyi ilgili fonksiyonlara yönlendirir.


        body(dict): Json formatında gelen bir dictionary, web tarafından gelen komutu ve ilgili alanları barındırır
        """

        command = body['command']

        if command == None:
            return
        else:
            await self.sendResponse()

        if command == "upload":
            await self.closeSerialMonitor()
        elif command == "openSerialMonitor":
            self.openSerialMontor(body["port"], body["baudRate"])
        elif command == "closeSerialMonitor":
            await self.closeSerialMonitor()
        elif command == "serialWrite":
            self.serialWrite(body["text"])


    def serialWrite(self, text):
        """
        Serial monitöre yazı yazdırır.


        text(str): serial monitöre yazılacak yazı
        """
        if self.serialOpen:
            logging.info(f"Writing to serial, data:{text}")
            self.ser.write(text.encode("utf-8"))

    def openSerialMontor(self, port, baudRate):
        """
        Serial monitörü açar.


        port(string): Kartın bağlı olduğu port

        baudRate(int):Serial monitör için baudrate
        """
        logging.info(f"Opening serial monitor")
        if not self.serialOpen:
            self.serialOpen = True

            self.ser = serial.Serial()
            self.ser.baudrate = baudRate
            self.ser.port = port

            if Data.boards[port].fqbn != config.deneyapMini:
                self.ser.setDTR(False)
                self.ser.setRTS(False)

            self.ser.open()

            # self.ser = serial.Serial(
            #     port=port,
            #     baudrate=baudRate,
            #     parity=serial.PARITY_NONE,
            #     stopbits=serial.STOPBITS_ONE,
            #     bytesize=serial.EIGHTBITS,
            #     timeout=0)

    async def sendResponse(self):
        """
        Web tarafına mesajın başarı ile alındığını geri bildirir.
        """
        bodyToSend = {"command": "response"}
        bodyToSend = json.dumps(bodyToSend)
        logging.info(f"SerialMonitorWebsocket sending response back")
        await self.websocket.send(bodyToSend)

    async def closeSerialMonitor(self):
        """
        Serial monitörü kapatır
        """
        logging.info(f"Closing serial monitor")
        if self.serialOpen and self.ser != None:
            self.ser.close()
            bodyToSend = {"command":"closeSerialMonitor"}
            bodyToSend = json.dumps(bodyToSend)
            await self.websocket.send(bodyToSend)

        self.serialOpen = False

    async def serialLog(self):
        """
        Serial monitörü okur ve websocket aracılığı ile web tarafına gönderir
        """
        if self.serialOpen and self.ser != None:
            try:
                waiting = self.ser.in_waiting
                line = self.ser.read(waiting).decode("utf-8")
            except serial.SerialException:
                await self.closeSerialMonitor()
                return
            except:
                return
            if line == "":
                return
            # print(line, end="")"
            bodyToSend = {"command":"serialLog", "log":line}
            bodyToSend = json.dumps(bodyToSend)
            await self.websocket.send(bodyToSend)

    async def mainLoop(self):
        """
        Ana döngü, her döngüde, web tarafından mesaj gelip gelmediğini kontrol eder, veri geldiyse commandParser()'a gönderir,
        aksi halde serial monitör açık ise serialLog()'u çalıştırır
        """
        while True:
            try:
                if not self.serialOpen:
                    await asyncio.sleep(.3)

                body = {"command":None}

                try:
                    message= await asyncio.wait_for(self.websocket.recv(), timeout=0.000001)
                    logging.info(f"SerialMonitorWebsocket received {message}")
                    body = json.loads(message)

                except (asyncio.TimeoutError, ConnectionRefusedError):
                    if self.serialOpen:
                        await self.serialLog()

                await self.commandParser(body)

            except Exception as e:
                logging.info("Serial Monitor Error")
                logging.exception("Because!: ")
                traceback.print_exc()
                bodyToSend = {"command": "serialLog", "log": str(e)+"\n"}
                bodyToSend = json.dumps(bodyToSend)
                await self.websocket.send(bodyToSend)