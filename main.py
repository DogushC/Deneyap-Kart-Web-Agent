import asyncio

import pystray
import websockets
from websockets.legacy import server

import config
from utils import Data
from Websocket import Websocket
from SerialMonitorWebsocket import SerialMonitorWebsocket
from pathlib import Path
import multiprocessing
import logging
from pystray import MenuItem, Icon
from PIL import Image
import threading
import _thread
import config as InitialConfig
from utils import createFolder, setupDeneyap
import os
import appdirs
import json
import sys
from ErrorGUI import showError
import webbrowser

def sysIconThread() -> None:
    """
    Function for threading.
    Creates system tray gui
    """
    def stop():
        logging.info("Exiting through icon")
        icon.stop()
        _thread.interrupt_main()

    menu = (MenuItem(f'Deneyap Kart Web Versiyonu: {Data.config["AGENT_VERSION"]}', lambda x:x, enabled=False),
            MenuItem(f'Deneyap Kütüphane Versiyonu: {Data.config["DENEYAP_VERSION"]}', lambda x: x, enabled=False),
            MenuItem('Siteye Git', goToWebsite),
            MenuItem('Kütüphanelere Git', goToLib),
            MenuItem('Log Dosyasını Aç', goToLogFile),
            MenuItem('Çıkış', stop), )
    image = Image.open("icon.ico")
    icon = Icon("name", image, "Deneyap Kart", menu)
    icon.run()

def goToWebsite() -> None:
    webbrowser.open("https://deneyapkart.org/deneyapkart/deneyapblok/")

def goToLib() -> None:
    os.startfile(Data.config['LIB_PATH'])

def goToLogFile():
    os.startfile(f"{Data.config['LOG_PATH']}")


def main(loop) -> None:
    Data.config = createConfig()

    #Create system tray
    thread = threading.Thread(target=sysIconThread)
    thread.daemon = True
    thread.start()

    logFile = f"{Data.config['LOG_PATH']}\deneyap.log"
    logging.basicConfig(handlers=[logging.FileHandler(filename=logFile, encoding='utf-8', mode='a+')], format='%(asctime)s-%(process)d-%(thread)d   %(levelno)d      %(message)s(%(funcName)s-%(lineno)d)', level=logging.INFO)
    logging.info(f"----------------------- Program Start Agent: v{Data.config['AGENT_VERSION']} Core: v{Data.config['DENEYAP_VERSION']}-----------------------")

    #Runs when first time installing or new version setup is run
    if Data.config['runSetup']:
        logging.info("Running Setup...")
        isSetupSuccess, message = setupDeneyap()
        if not isSetupSuccess:
            logging.critical("Setup exited with error. Exiting program")
            showError(f"Deneyap Kart kütüphaneleri indirilirken hata oluştu.\n\n{message}")
            return

    createFolder(Data.config["LOG_PATH"])
    createFolder(Data.config["TEMP_PATH"])


    try:
        #Websocket for normal communication between agent and front-end
        start_server = websockets.serve(Websocket, 'localhost', 49182)
        loop.run_until_complete(start_server)
        logging.info("Main Websocket is ready")

        #Websocket for serial monitor communication between agent and front-end
        #when serial monitor is constantly used without delay, it blocks normal communication which is more important
        start_serial_server = websockets.serve(SerialMonitorWebsocket, 'localhost', 49183)
        loop.run_until_complete(start_serial_server)
        logging.info("Serial Websocket is ready")

    except OSError:
        showError("Program Zaten Çalışıyor.")
        raise

    try:
        logging.info("Running Forever...")
        loop.run_forever()

    except Exception as e:
        logging.exception("InMain: ")
    finally:
        logging.info("Exiting Program")



def createConfig() -> dict:
    """
    Creates config file if newly installed. if it exist updates it and changes runSetup to true.

    :return: config file data, which will be passed to Data class
    :rtype: dict
    """

    Path(InitialConfig.LOG_PATH).mkdir(parents=True, exist_ok=True)

    isConfigExists = os.path.exists(f'{InitialConfig.CONFIG_PATH}\config.json')
    configFileData = {
        "deneyapKart": "dydk_mpv10",
        "deneyapMini": "dym_mpv10",
        "deneyapKart1A": "dydk1a_mpv10",
        "deneyapKartG": "dyg_mpv10",
        "deneyapMiniv2": "dym_mpv20",
        "deneyapKart1Av2": "dydk1a_mpv20",

        "AGENT_VERSION": InitialConfig.AGENT_VERSION,
        "DENEYAP_VERSION": InitialConfig.DENEYAP_VERSION,

        "TEMP_PATH": InitialConfig.TEMP_PATH,
        "CONFIG_PATH": InitialConfig.CONFIG_PATH,
        "LOG_PATH": InitialConfig.LOG_PATH,
        "LIB_PATH": InitialConfig.LIB_PATH,

        "runSetup": True
    }

    if not isConfigExists:#if it is first install
        configFileDataString = json.dumps(configFileData)
        with open(f"{configFileData['CONFIG_PATH']}\config.json", "w") as configFile:
            configFile.write(configFileDataString)
    else:
        #loads old config file
        with open(f"{configFileData['CONFIG_PATH']}\config.json", "r") as configFile:
            configFileDataString = configFile.read()
            configFileDataOld = json.loads(configFileDataString)
            for k in configFileData.keys(): #checks if new key is added.
                if not k in configFileDataOld:
                    configFileDataOld[k] = configFileData[k]
                    if k == "AGENT_VERSION":
                        #some old version did not have old agent version, if left a sconfigFileDataOld[k] = configFileData[k]
                        #causes it to not understand version change so does not run setup
                        configFileDataOld[k] = "0.0.0"

            configFileData = configFileDataOld
            version = configFileData['AGENT_VERSION'] if "AGENT_VERSION" in configFileData else "0.0.0" #i don't know why i double checked it, leaving it just in case
            #updating config file for new version
            configFileData['DENEYAP_VERSION'] = configFileData['DENEYAP_VERSION'] if "DENEYAP_VERSION" in configFileData else InitialConfig.DENEYAP_VERSION
            configFileData['AGENT_VERSION'] = InitialConfig.AGENT_VERSION
            configFileData['LIB_PATH'] = configFileData['LIB_PATH'] if "LIB_PATH" in configFileData else InitialConfig.LIB_PATH


            if (version != InitialConfig.AGENT_VERSION): #if new version, runs setup and updates config file
                configFileData['runSetup'] = True
                configFileDataString = json.dumps(configFileData)
                with open(f"{configFileData['CONFIG_PATH']}\config.json", "w") as configFile:
                    configFile.write(configFileDataString)
    return configFileData


if __name__ == '__main__':

    multiprocessing.freeze_support() #need for pyinstaller

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        main(loop)
    except:
        logging.exception("Main Error: ")
    finally:
        for websocket in Data.websockets:
            websocket.closeSocket()
        loop.stop()

    sys.exit()
