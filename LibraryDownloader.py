from utils import executeCli

def searchLibrary(seartTerm:str) -> str:
    result = executeCli(f"lib search {seartTerm} --format json")
    return result

def installLibrary(name:str, version:str) -> str:
    result = executeCli(f"lib install {name}@{version}")
    return result

def installLibraryZip(zipPath:str) -> str:
    pass
    #TODO install from zip



