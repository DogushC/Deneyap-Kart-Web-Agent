import random
from utils import Data, createInoFile, executeCliPipe, executeCli
import config
import json
import logging

class Board:
    def __init__(self, boardName, fqbn, port):
        self.boardName = boardName
        self.fqbn = fqbn
        self.port = port
        self.ID = random.randint(1000000, 9999999)
        logging.info(f"Board with Name:{boardName}, FQBN:{fqbn}, Port:{port}, ID:{self.ID} is created")

    def uploadCode(self, code, fqbn = None):
        logging.info(f"Uploading code to {self.ID}")
        fqbn = fqbn if fqbn != None else self.fqbn
        createInoFile(code)
        pipe = executeCliPipe(f"compile --port {self.port} --upload --fqbn {fqbn} {config.TEMP_PATH}/tempCode")
        return pipe

    def compileCode(self, code, fqbn = None):
        logging.info(f"Compiling code for {self.ID}")
        fqbn = fqbn if fqbn != None else self.fqbn
        createInoFile(code)
        pipe = executeCliPipe(f"compile --fqbn {fqbn} {config.TEMP_PATH}/tempCode")
        return pipe

    @staticmethod
    def refreshBoards():
        logging.info(f"Refresing Boards")
        boardListString = executeCli("board list --format json")
        boardsJson = json.loads(boardListString)
        Data.boards = {}
        for boardJson in boardsJson:
            if "matching_boards" in boardJson:
                boardName = boardJson["matching_boards"][0]["name"]  # TODO investigate why index 0?
                boardId = boardJson["matching_boards"][0]["fqbn"]
            else:
                boardName = "Deneyap Kart"
                boardId = "deneyap:esp32:dydk_mpv10"

            boardPort = boardJson["port"]["address"]
            logging.info(f"Found board with Name:{boardName}, FQBN:{boardId}, Port:{boardPort}")
            board = Board(boardName, boardId, boardPort)
            Data.boards[board.ID] = board

    @staticmethod
    async def sendBoardInfo(websocket):
        body = {"command": "returnBoards", "boards": []}
        for k, v in Data.boards.items():
            body['boards'].append({"boardName": v.boardName, "port": v.port, "ID": v.ID})
        body = json.dumps(body)
        logging.info(f"Sending {body}")
        await websocket.send(body)


    def __repr__(self):
        return f"{self.boardName} on port: {self.port} with fqbn of {self.fqbn} and ID of :{self.ID}"
