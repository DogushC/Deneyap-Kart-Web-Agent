import subprocess
from utils import Data, createInoFile, executeCliPipe, executeCli
import config
import json
import logging
import websockets

class Board:
    """
    Bilgisayara takılan bir kartı temsil eder.


    boardName (str): Kartın adı (Deneyap Kart ya da Deneyap Mini)

    fqbn (str): fully qualified board name, arduino-cli'in kartı gördüğü isim

    port (str): kartın bağlı olduğu port

    ID (int): karta atanan rastgele id, (1000000 - 9999999) arası, web tarafında eşlemek için kullanılır
    """
    def __init__(self, boardName: str, fqbn: str, port:str):
        self.boardName = boardName
        self.fqbn = fqbn
        self.port = port
        logging.info(f"Board with Name:{boardName}, FQBN:{fqbn}, Port:{port} is created")

    def uploadCode(self, code:str, fqbn:str, uploadOptions:str) -> subprocess.PIPE:
        """
        Kodu karta yükleyen fonksiyon


        code (str): web tarafından gelen kod

        fqbn (str): kodun arduino-cli tarafında ki adı
        """
        logging.info(f"Uploading code to {self.boardName}:{self.port}")
        createInoFile(code)
        pipe = executeCliPipe(f"compile --port {self.port} --upload --fqbn {fqbn}:{uploadOptions} {config.TEMP_PATH}/tempCode")
        return pipe

    @staticmethod
    def compileCode(code:str, fqbn:str, uploadOptions:str) -> subprocess.PIPE:
        """
        Kodu derleyen fonksiyon


        code (str): web tarafından gelen kod

        fqbn (str): kodun arduino-cli tarafında ki adı
        """
        logging.info(f"Compiling code for {fqbn}")
        createInoFile(code)
        pipe = executeCliPipe(f"compile --fqbn {fqbn}:{uploadOptions} {config.TEMP_PATH}/tempCode")
        return pipe

    @staticmethod
    def refreshBoards() -> None:
        """
        bilgisayara bağlı olan kartları kontrol eder ve Data class'ını günceller
        """
        logging.info(f"Refresing Boards")
        boardListString = executeCli("board list --format json")
        boardsJson = json.loads(boardListString)
        Data.boards = {}
        for boardJson in boardsJson:
            if "matching_boards" in boardJson:
                boardName = boardJson["matching_boards"][0]["name"]  # TODO investigate why index 0?
                boardId = boardJson["matching_boards"][0]["fqbn"]
            else:
                boardName = "Unknown"
                boardId = ""

            boardPort = boardJson["port"]["address"]
            logging.info(f"Found board with Name:{boardName}, FQBN:{boardId}, Port:{boardPort}")
            board = Board(boardName, boardId, boardPort)
            Data.boards[boardPort] = board

    @staticmethod
    async def sendBoardInfo(websocket: websockets) -> None: #TODO it is not websockets but websocket connection, do proper typing
        """
        Bilgisayara bağlı olan kartları websocket aracılığı ile web'e gönderir.


        websocket (websocket): web tarafı iletişime geçmeyi sağlayan websocket objesi.
        """
        body = {"command": "returnBoards", "boards": []}
        for k, v in Data.boards.items():
            body['boards'].append({"boardName": v.boardName, "port": v.port})
        body = json.dumps(body)
        logging.info(f"Sending {body}")
        await websocket.send(body)


    def __repr__(self) -> str:
        return f"{self.boardName} on port: {self.port} with fqbn of {self.fqbn}"
