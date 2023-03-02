import json
import subprocess
import config as InitialConfig
from pathlib import Path
import logging
from DownloadGUI import startGUI
from multiprocessing import Process

class Data:
    """
    keeps data on runtime
    """
    boards  = {}
    threads = []
    config = {}
    websockets = []
    processes = []

    @staticmethod
    def updateConfig():
        """
        update config files to make changes permenant.
        """
        logging.info("config file is changing, new file: ", Data.config)
        configFileDataString = json.dumps(Data.config)
        with open(f"{Data.config['CONFIG_PATH']}\config.json", "w") as configFile:
            configFile.write(configFileDataString)
        logging.info("config file changed successfully.")

def executeCli(command:str) -> str:
    """
    runs command for arduino-cli, waits until arduino-cli returns then returns its output.

    :param command: command that will run, basicly executeCli("config init") --> runs "arduino-cli config init" on cmd
    :type command: str

    :return: output from arduino-cli, depended of command.
    :rtype: str
    """

    logging.info(f"Executing command arduino-cli {command}")
    returnString = subprocess.check_output(f"arduino-cli {command}", shell=True)
    return returnString.decode("utf-8")

def executeCliPipe(command:str) -> subprocess.Popen:
    """
    runs command for arduino-cli, does not wait for response instead returns subprocess.

    :param command: command that will run, basicly executeCliPipe("config init") --> runs "arduino-cli config init" on cmd
    :type command: str

    :return: subprocess of command that run for accessing output live.
    :rtype: subprocess.Popen
    """
    logging.info(f"Executing pipe command arduino-cli {command}")
    pipe = subprocess.Popen(f"arduino-cli {command}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return pipe


def executeCli2Pipe(command:str) -> subprocess.Popen:
    """
    runs command for arduino-cli, does not wait for response instead returns subprocess.

    :param command: command that will run, basicly executeCliPipe("config init") --> runs "arduino-cli config init" on cmd
    :type command: str

    :return: subprocess of command that run for accessing output and error live.
    :rtype: subprocess.Popen
    """
    logging.info(f"Executing pipe command arduino-cli {command}")
    pipe = subprocess.Popen(f"arduino-cli {command}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return pipe

def createFolder(fileDir:str) -> None:
    """
    creates new folder, if it exist does not do anything

    :param fileDir: directory and name of the folder that will be created
    :type fileDir: str
    """

    logging.info(f"Creating folder {fileDir}")
    Path(fileDir).mkdir(parents=True, exist_ok=True)

def createInoFile(code:str) -> None:
    """
    creates .ino file for arduino-cli to compile and upload code.

    :param code: code that will be written to file. send by front-end
    :type code: str
    """

    tempPath = Data.config["TEMP_PATH"]
    logging.info(f"Creating Ino file at {tempPath}")
    createFolder(tempPath)
    createFolder(f"{tempPath}/tempCode")
    with open(f"{tempPath}/tempCode/tempCode.ino", "w", encoding="utf-8") as inoFile:
        inoFile.writelines(code)
        logging.info(f"File created")


def updateIndex() -> str:
    """
    updates arduino-cli index. in order to renew libraries

    :return: result of 'arduino-cli update' command
    :rtype: str
    """
    logging.info("updating index")
    pipe = executeCli2Pipe(f"update")
    return pipe.communicate()[1].decode("utf-8")

def downloadCore(version:str)->str:
    """
    :param version: version of deneyapkart core that will be downloaded.
    :type version: str

    :return: output of 'arduino-cli core install'
    :rtype: str
    """
    logging.info(f"installing deneyap:esp32@{version}")
    pipe = executeCli2Pipe(f"core install deneyap:esp32@{version}")
    return pipe.communicate()[1].decode("utf-8")

def setupDeneyap() -> (bool, str):
    """
    runs when program first downloaded or updated.
    configures deneyap kart to arduino-cli
    downloads some libraries

    :return: first element is whetever setup was success or not, second element is error message.
    :rtype: (bool, str)
    """

    process = Process(target=startGUI)
    process.start()

    try:
        executeCli("config init")
    except:
        logging.info(f"Init file does exist skipping this step")
    else:
        logging.info(f"Init file created")

    string = executeCli("config dump")
    if not ("deneyapkart" in string):
        logging.info("package_deneyapkart_index.json is not found on config, adding it")
        executeCli("config add board_manager.additional_urls https://raw.githubusercontent.com/deneyapkart/deneyapkart-arduino-core/master/package_deneyapkart_index.json")
        logging.info("added package_deneyapkart_index.json to config")
    if not ("DeneyapKartWeb" in string):
        logging.info("directories is not set, setting it.")
        executeCli(f"config set directories.data {Data.config['CONFIG_PATH']}")
        executeCli(f"config set directories.downloads {Data.config['CONFIG_PATH']}\staging")
        executeCli(f"config set directories.user {Data.config['CONFIG_PATH']}\packages\deneyap\hardware\esp32\{Data.config['DENEYAP_VERSION']}\ArduinoLibraries")
        logging.info("directories are changed")
    else:
        logging.info("package_deneyapkart_index.json is found on config skipping this step")

    t = updateIndex()
    if t:
        logging.critical(t)
        process.terminate()
        return False,t

    t = downloadCore(Data.config['DENEYAP_VERSION'])
    if t:
        logging.critical(t)
        process.terminate()
        return False,t

    #TODO this part will be added as default to core + adafruit color thingy.
    pipe = executeCli2Pipe("lib install Stepper IRremote")
    t = pipe.communicate()[1].decode("utf-8")
    if t:
        logging.critical(t)
        process.terminate()
        return False,t

    Data.config['runSetup'] = False
    Data.config['AGENT_VERSION'] = InitialConfig.AGENT_VERSION
    configDataString = json.dumps(Data.config)
    with open(f"{Data.config['CONFIG_PATH']}\config.json", 'w') as configFile:
        logging.info(f"Config File Changed")
        configFile.write(configDataString)

    process.terminate()
    return True,1
