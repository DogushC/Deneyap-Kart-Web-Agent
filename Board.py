import subprocess
from utils import Data, createInoFile, executeCliPipe, executeCli
import config
import json
import logging
import websockets


class Board:
    """
    Represents a deneyap kart that plugged to computer

    boardName (str): Kartın adı (Deneyap Kart ya da Deneyap Mini)
    fqbn (str): fully qualified board name, arduino-cli'in kartı gördüğü isim
    port (str): kartın bağlı olduğu port
    ID (int): karta atanan rastgele id, (1000000 - 9999999) arası, web tarafında eşlemek için kullanılır
    """
    def __init__(self, boardName: str, fqbn: str, port:str)->None:
        """
        :param boardName: board name, currently Deneyap Kart or Deneyap Mini
        :type boardName: str

        :param fqbn: fully qualified board name, board name that recognized by arduino-cli
            deneyap:esp32:dydk_mpv10 for Deneyap Kart
            deneyap:esp32:dym_mpv10 for Deneyap Mini
        :type fqbn: str

        :param port: COM port that board connected to like COM4
        :type port: str

        Deneyap mini is not recognized by Windows 10, so it is taken as Unknown.
        """

        self.boardName = boardName
        self.fqbn = fqbn
        self.port = port
        logging.info(f"Board with Name:{boardName}, FQBN:{fqbn}, Port:{port} is created")

    def uploadCode(self, code:str, fqbn:str, uploadOptions:str) -> subprocess.Popen:
        """
        Compiles and uploads code to board

        :param code: code that sent by front-end
        :type code: str

        :param fqbn: fully qualified board name, board name that recognized by arduino-cli
            deneyap:esp32:dydk_mpv10 for Deneyap Kart
            deneyap:esp32:dym_mpv10 for Deneyap Mini
        :type fqbn: str

        :param uploadOptions: upload options for board. it is board spesific and sent by front-end as parsed.
        :type uploadOptions: str


        :return: returns subprocess.Popen object to write output to front-end
        :rtype: subprocess.Popen
        """

        logging.info(f"Uploading code to {self.boardName}:{self.port}")
        createInoFile(code) #create Ino file so arduino-cli can read it to compile and upload to board
        pipe = executeCliPipe(f"compile --port {self.port} --upload --fqbn {fqbn}:{uploadOptions} {config.TEMP_PATH}/tempCode")
        return pipe

    @staticmethod
    def compileCode(code:str, fqbn:str, uploadOptions:str) -> subprocess.Popen:
        """
        compiles code

        :param code: code that sent by front-end
        :type code: str

        :param fqbn: fully qualified board name, board name that recognized by arduino-cli
            deneyap:esp32:dydk_mpv10 for Deneyap Kart
            deneyap:esp32:dym_mpv10 for Deneyap Mini
        :type fqbn: str

        :param uploadOptions: upload options for board. it is board spesific and sent by front-end as parsed.
        :type uploadOptions: str

        :return: returns subprocess.Popen object to write output to front-end
        :rtype: subprocess.Popen
        """

        logging.info(f"Compiling code for {fqbn}")
        createInoFile(code)  #create Ino file so arduino-cli can read it to compile
        pipe = executeCliPipe(f"compile --fqbn {fqbn}:{uploadOptions} {config.TEMP_PATH}/tempCode")
        return pipe

    @staticmethod
    def refreshBoards() -> None:
        """
        Checks connected devices and append them to Data class for later use
        """

        logging.info(f"Refresing Boards")
        boardListString = executeCli("board list --format json")
        boardsJson = json.loads(boardListString)
        Data.boards = {}
        for boardJson in boardsJson:
            if "matching_boards" in boardJson:
                boardName = boardJson["matching_boards"][0]["name"]  # TODO investigate why index 0?
                boardId = boardJson["matching_boards"][0]["fqbn"]
            else:#deneyap mini is goes in to here.
                boardName = "Unknown"
                boardId = ""

            boardPort = boardJson["port"]["address"]
            logging.info(f"Found board with Name:{boardName}, FQBN:{boardId}, Port:{boardPort}")
            board = Board(boardName, boardId, boardPort)
            Data.boards[boardPort] = board

    @staticmethod
    async def sendBoardInfo(websocket: websockets.legacy.server.WebSocketServerProtocol) -> None:
        """
        sends all board info to front-end via websocket

        :param websocket: websocket connection to front-end
        :type websocket: websockets.legacy.server.WebSocketServerProtocol
        """

        body = {"command": "returnBoards", "boards": []}
        for k, v in Data.boards.items():
            body['boards'].append({"boardName": v.boardName, "port": v.port})
        body = json.dumps(body)
        logging.info(f"Sending {body}")
        await websocket.send(body)


    def __repr__(self) -> str:
        return f"{self.boardName} on port: {self.port} with fqbn of {self.fqbn}"
