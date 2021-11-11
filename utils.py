import json
import subprocess
from pathlib import Path
import logging

class Data:
    """
    Program içerisinde geçici olarak tutulacak verileri tutar
    """
    boards  = {}
    threads = []
    config = {}
    websockets = []

def executeCli(command):
    """
    verilen komutu çalıştırır, komut bitene kadar programı bekletir ve çıktıyı döner.


    command(str): cmd'ye yazılacak komut, arduino-cli kısmı hariç

    bknz: executeCli("config init") --> cmd ekranına "arduino-cli config init" yazdıracaktır
    """
    logging.info(f"Executing command arduino-cli {command}")
    returnString = subprocess.check_output(f"arduino-cli {command}", shell=True)
    return returnString.decode("utf-8")

def executeCliPipe(command):
    """
    verilen komutu çalıştırır, komutun bitmesini beklemez, komutun çalıştığı process ile olan pipe'ı döner.


    command(str): cmd'ye yazılacak komut, arduino-cli kısmı hariç

    bknz: executeCli("config init") --> cmd ekranına "arduino-cli config init" yazdıracaktır
    """
    logging.info(f"Executing pipe command arduino-cli {command}")
    pipe = subprocess.Popen(f"arduino-cli {command}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return pipe

def createFolder(fileDir):
    """
    Yeni klasör oluşturur. Eğer var ise, bir değişiklik yapmaz


    fileDir(str):oluşturulacak klasörün yolu
    """
    logging.info(f"Creating folder {fileDir}")
    Path(fileDir).mkdir(parents=True, exist_ok=True)

def createInoFile(code):
    """
    .ino dosyasını geçici klasörün içerisine oluşturur.


    code(str): kayıt edilecek kod
    """
    tempPath = Data.config["TEMP_PATH"]
    logging.info(f"Creating Ino file at {tempPath}")
    createFolder(tempPath)
    createFolder(f"{tempPath}/tempCode")
    with open(f"{tempPath}/tempCode/tempCode.ino", "w") as inoFile:
        inoFile.writelines(code)
        logging.info(f"File created")


def setupDeneyap():
    """
    Program ilk yüklendiğinde çalıştırılır, arduino-cli'in konfigurasyonunu yapar, deneyap kartı arduino-cli'a ekler ve yükler.
    """
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
    executeCli("lib install Stepper HCSR04 IRremote")

    Data.config['runSetup'] = False
    configDataString = json.dumps(Data.config)
    with open(f"{Data.config['CONFIG_PATH']}\config.json", 'w') as configFile:
        logging.info(f"Config File Changed")
        configFile.write(configDataString)


