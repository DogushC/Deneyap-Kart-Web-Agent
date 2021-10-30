import json
import subprocess
from pathlib import Path
import logging

class Data:
    boards  = {}
    threads = []
    config = {}

def executeCli(command):
    logging.info(f"Executing command arduino-cli {command}")
    returnString = subprocess.check_output(f"arduino-cli {command}", shell=True)
    return returnString.decode("utf-8")

def executeCliPipe(command):
    logging.info(f"Executing pipe command arduino-cli {command}")
    pipe = subprocess.Popen(f"arduino-cli {command}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return pipe

def createFolder(fileDir):
    logging.info(f"Creating folder {fileDir}")
    Path(fileDir).mkdir(parents=True, exist_ok=True)

def createInoFile(code):
    tempPath = Data.config["TEMP_PATH"]
    logging.info(f"Creating Ino file at {tempPath}")
    createFolder(tempPath)
    createFolder(f"{tempPath}/tempCode")
    with open(f"{tempPath}/tempCode/tempCode.ino", "w") as inoFile:
        inoFile.writelines(code)
        logging.info(f"File created")


def setupDeneyap():
    try:
        executeCli("config init")
    except:
        logging.info(f"Init file does exist skipping this step")
    else:
        logging.info(f"Init file created")


    string = executeCli("config dump")
    if not ("deneyapkart" in string):
        executeCli("config add board_manager.additional_urls https://raw.githubusercontent.com/deneyapkart/deneyapkart-arduino-core/master/package_deneyapkart_index.json")

    executeCli("core install deneyap:esp32")

    Data.config['runSetup'] = False
    configDataString = json.dumps(Data.config)
    with open(f"{Data.config['CONFIG_PATH']}\config.json", 'w') as configFile:
        logging.info(f"Config File Changed")
        configFile.write(configDataString)


