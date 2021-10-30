import asyncio
import json
import serial
import logging

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

    async def __init__(self, websocket, path):
        logging.info(f"SerialMonitorWebsocket is object created")

        self.websocket = websocket
        self.serialOpen = False

        await self.mainLoop()

    async def commandParser(self, body):


        command = body['command']

        if command == None:
            return
        else:
            await self.sendResponse()

        if command == "upload":
            self.closeSerialMonitor()
        elif command == "openSerialMonitor":
            self.openSerialMontor(body["port"], body["baudRate"])
        elif command == "closeSerialMonitor":
            self.closeSerialMonitor()
        elif command == "serialWrite":
            self.serialWrite(body["text"])


    def serialWrite(self, text):
        if self.serialOpen:
            logging.info(f"Writing to serial, data:{text}")
            self.ser.write(text.encode("utf-8"))

    def openSerialMontor(self, port, baudRate):
        logging.info(f"Opening serial monitor")
        if not self.serialOpen:

            self.serialOpen = True
            self.ser = serial.Serial(
                port=port,
                baudrate=baudRate,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=0)

    async def sendResponse(self):
        bodyToSend = {"command": "response"}
        bodyToSend = json.dumps(bodyToSend)
        logging.info(f"SerialMonitorWebsocket sending response back")
        await self.websocket.send(bodyToSend)

    def closeSerialMonitor(self):
        logging.info(f"Closing serial monitor")
        if self.serialOpen:
            self.ser.close()
        self.serialOpen = False

    async def serialLog(self):
        waiting = self.ser.in_waiting
        try:
            line = self.ser.read(waiting).decode("utf-8")
        except:
            return
        if line == "":
            return
        # print(line, end="")"
        bodyToSend = {"command":"log", "log":line}
        bodyToSend = json.dumps(bodyToSend)
        await self.websocket.send(bodyToSend)

    async def mainLoop(self):
        try:
            while True:
                body = {"command":None}

                try:
                    message= await asyncio.wait_for(self.websocket.recv(), timeout=0.000001)
                    logging.info(f"SerialMonitorWebsocket received {message}")
                    body = json.loads(message)

                except (asyncio.TimeoutError, ConnectionRefusedError):
                    if self.serialOpen:
                        await self.serialLog()

                await self.commandParser(body)

        finally:
            print("Closing Thread!!")