"""
Main dosyası, Programın giriş noktası
"""

import asyncio
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

def sysIconThread() -> None:
    """
    Ayrı bir thread'de system tray için gui oluşturur.
    """
    def stop():
        logging.info("Exiting through icon")
        icon.stop()
        _thread.interrupt_main()

    menu = (MenuItem('Exit', stop),)
    image = Image.open("icon.ico")
    icon = Icon("name", image, "Deneyap Kart", menu)
    icon.run()

def main() -> None:
    """
    Programın ilk çalışan fonksiyonu, system tray gui'ını, configurasyonu ve websocket server'larını çalıştırır
    """
    thread = threading.Thread(target=sysIconThread)
    thread.daemon = True
    thread.start()

    Data.config = createConfig()

    logFile = f"{Data.config['LOG_PATH']}\deneyap.log"
    logging.basicConfig(filename=logFile, filemode='a+', format='%(asctime)s-%(process)d-%(thread)d   %(levelno)d      %(message)s(%(funcName)s-%(lineno)d)', level=logging.INFO)
    logging.info(f"----------------------- Program Start v{Data.config['version']}-----------------------")


    if Data.config['runSetup']:
        isSetupSuccess = setupDeneyap()
        if not isSetupSuccess:
            logging.critical("Setup exited with error. Exiting program")
            showError("Deneyap Kart kütüphaneleri indirilirken hata oluştu.")
            return

    createFolder(Data.config["LOG_PATH"])
    createFolder(Data.config["TEMP_PATH"])


    start_server = websockets.serve(Websocket, 'localhost', 49182)
    asyncio.get_event_loop().run_until_complete(start_server)
    logging.info("Main Websocket is ready")

    start_serial_server = websockets.serve(SerialMonitorWebsocket, 'localhost', 49183)
    asyncio.get_event_loop().run_until_complete(start_serial_server)
    logging.info("Serial Websocket is ready")


    try:
        logging.info("Running Forever...")
        asyncio.get_event_loop().run_forever()

    except Exception as e:
        logging.exception("InMain: ")
    finally:
        logging.info("Exiting Program")



def createConfig() -> None:
    """
    İlk çalışmada config dosyasını oluşturur, eğer var ise, programa yükler.
    """
    Path(InitialConfig.LOG_PATH).mkdir(parents=True, exist_ok=True)

    isConfigExists = os.path.exists(f'{InitialConfig.CONFIG_PATH}\config.json')
    if not isConfigExists:
        configFileData = {
                "deneyapKart" : "deneyap:esp32:dydk_mpv10",
                "deneyapMini" : "deneyap:esp32:dym_mpv10",
                "version": InitialConfig.version,

                "TEMP_PATH" : f"{appdirs.user_data_dir()}\DeneyapKartWeb\Temp",
                "CONFIG_PATH" : f"{appdirs.user_data_dir()}\DeneyapKartWeb",
                "LOG_PATH" : f"{appdirs.user_data_dir()}\DeneyapKartWeb",
                "runSetup": True
            }
        configFileDataString = json.dumps(configFileData)
        with open(f"{appdirs.user_data_dir()}\DeneyapKartWeb\config.json", "w") as configFile:
            configFile.write(configFileDataString)
    else:
        with open(f"{appdirs.user_data_dir()}\DeneyapKartWeb\config.json", "r") as configFile:
            configFileDataString = configFile.read()
            configFileData = json.loads(configFileDataString)
            version = configFileData['version'] if "version" in configFileData else "0.0.0"
            if (version != InitialConfig.version):
                configFileData = {
                    "deneyapKart": "deneyap:esp32:dydk_mpv10",
                    "deneyapMini": "deneyap:esp32:dym_mpv10",
                    "version": InitialConfig.version,

                    "TEMP_PATH": f"{appdirs.user_data_dir()}\DeneyapKartWeb\Temp",
                    "CONFIG_PATH": f"{appdirs.user_data_dir()}\DeneyapKartWeb",
                    "LOG_PATH": f"{appdirs.user_data_dir()}\DeneyapKartWeb",
                    "runSetup": True
                }
                configFileDataString = json.dumps(configFileData)
                with open(f"{appdirs.user_data_dir()}\DeneyapKartWeb\config.json", "w") as configFile:
                    configFile.write(configFileDataString)

    return configFileData



if __name__ == '__main__':

    # Pyinstaller fix
    multiprocessing.freeze_support()

    try:
        main()
    except:
        pass
    finally:
        logging.exception("Main Error: ")
        for websocket in Data.websockets:
            websocket.closeSocket()
        asyncio.get_event_loop().stop()

    sys.exit()
