import asyncio
import json
import subprocess

import config
from DeviceChecker import DeviceChecker
from utils import Data, downloadCore
from Board import Board
from multiprocessing import Queue
import logging
from websockets.exceptions import ConnectionClosedOK
import websockets

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


class Websocket(aobject):
    """
    Ana websocket'in çalıştığı sınıf, her bir sites bağlantısı için bir websocket objesi oluşturulur.


    websocket(websocket): web tarafı ile yapılan socket bağlantısının objesi

    path(str):
    """
    async def __init__(self, websocket: websockets, path:str): #TODO proper websocket typing
        logging.info(f"Websocket object is created")
        Data.websockets.append(self)
        self.websocket = websocket

        self.queue = Queue()

        self.deviceChecker = DeviceChecker(self.queue)
        self.deviceChecker.start()

        await self.mainLoop()

    async def readAndSend(self, pipe: subprocess.PIPE) -> None:
        """
        daha önceden açılmış olan pipe'tan  veriyi okur ve websocket aracılığı ile web tarafına gönderir.


        pipe(subprocess.Popen()): verinin okunacağı pipe
        """
        allText = ""
        for c in iter(lambda: pipe.stdout.read(1), b''):
            t = c.decode("utf-8")
            allText += t
            bodyToSend = {"command": "consoleLog", "log": t}
            bodyToSend = json.dumps(bodyToSend)
            await self.websocket.send(bodyToSend)
            await asyncio.sleep(0)

        t = pipe.communicate()[1].decode("utf-8")
        allText += t
        bodyToSend = {"command": "consoleLog", "log": t}
        bodyToSend = json.dumps(bodyToSend)
        logging.info(f"Pipe output {allText}")
        await self.websocket.send(bodyToSend)

    async def commandParser(self, body: dict) -> None:
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
            await self.upload(body['board'], body['port'], body["code"])
        elif command == "compile":
            await self.compile(body['board'], body["code"])
        elif command == "getBoards":
            await self.getBoards()
        elif command == "getVersion":
            await self.getVersion()
        elif command == "changeVersion":
            await self.changeVersion(body['version'])

    async def changeVersion(self, version):
        #TODO trigger this function from web, example body {command:changeVersion, version:1.3.2}
        logging.info(f"Changing version to {version}")
        error = downloadCore(version)
        bodyToSend = {"command":"versionChange", "success":True}
        if error:
            logging.info("Version cant be downloaded")
            logging.info(error)
            bodyToSend["success"] = False
        await self.websocket.send(bodyToSend)

    def setUploadOptions(self, uploadMode = "auto", uploadSpeed = 921600, CPUFreq=240, flashFreq = 90, flasMode="QIO", partitionScheme="default", debugLevel="None"):

        pass

    async def sendResponse(self) -> None:
        """
        Web tarafına mesajın başarı ile alındığını geri bildirir.
        """
        logging.info(f"Main Websocket sending response back")
        bodyToSend = {"command": "response"}
        bodyToSend = json.dumps(bodyToSend)
        await self.websocket.send(bodyToSend)


    async def upload(self, boardName:str, port:str, code:str) -> None:
        """
        Kodun karta yüklenmesi için Board.uploadCode() fonksiyonunu çalştıran fonksiyon


        ID (int): kodun yükleneceği kartın ID'si

        code (str): kodun kendisi.
        """
        board = Data.boards[port]
        if boardName == "Deneyap Mini":
            pipe = board.uploadCode(code, config.deneyapMini)
        elif boardName == "Deneyap Kart":
            pipe = board.uploadCode(code, config.deneyapKart)
        else:
            logging.warning(f"Specified Board is not found. Board name: {board.boardName}")
            return

        bodyToSend = {"command": "cleanConsoleLog", "log": ""}
        bodyToSend = json.dumps(bodyToSend)
        await self.websocket.send(bodyToSend)
        await self.readAndSend(pipe)

    async def getVersion(self) -> None:
        """
        Versiyonu Webe Gönderir
        """
        bodyToSend = {"command": "returnVersion", "version": config.AGENT_VERSION}
        bodyToSend = json.dumps(bodyToSend)
        await self.websocket.send(bodyToSend)

    async def compile(self, boardName:str, code:str) -> None:
        """
        Kodun derlenmesi için Board.compileCode() fonksiyonunu çalştıran fonksiyon


        ID (int): kodun yükleneceği kartın ID'si

        code (str): kodun kendisi.
        """
        if boardName == "Deneyap Mini":
            pipe = Board.compileCode(code, config.deneyapMini)
        elif boardName == "Deneyap Kart":
            pipe = Board.compileCode(code, config.deneyapKart)
        else:
            logging.warning(f"Specified Board is not found. Board name: {boardName}")
            return

        bodyToSend = {"command": "cleanConsoleLog", "log": "Compling Code...\n"}
        bodyToSend = json.dumps(bodyToSend)
        await self.websocket.send(bodyToSend)
        await self.readAndSend(pipe)

    async def getBoards(self) -> None:
        """
        Bilgisayara takılı olan güncel kartları web tarafına gönderir.
        """
        Board.refreshBoards()
        await Board.sendBoardInfo(self.websocket)

    def closeSocket(self) -> None:
        logging.info("Closing DeviceChecker")
        self.deviceChecker.terminate()
        self.deviceChecker.process.join()
        logging.info("DeviceChecker Closed")

    async def mainLoop(self) -> None:
        """
        Ana döngü, her döngüde, web tarafından mesaj gelip gelmediğini kontrol eder, veri geldiyse commandParser()'a gönderir,
        aksi halde queue'de ki komutları kontrol eder.
        """
        try:
            while True:
                body = {"command":None}

                try:
                    message=await asyncio.wait_for(self.websocket.recv(), timeout=0.1)
                    logging.info(f"Main Websocket received {message}")
                    body = json.loads(message)
                except (asyncio.TimeoutError, ConnectionRefusedError):
                    if not self.queue.empty():
                        body = self.queue.get()
                except Exception:
                    logging.exception("Main Websocket recv error: ")
                    await self.websocket.close()
                    logging.info("Websocket is closed")
                    break

                await self.commandParser(body)
        except:
            logging.exception("Websocket Mainloop: ")
        finally:
            self.deviceChecker.terminate()
            self.deviceChecker.join()