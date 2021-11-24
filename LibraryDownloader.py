from utils import executeCli

def searchLibrary(seartTerm):
    result = executeCli(f"lib search {seartTerm} --format json")
    return result

def installLibrary(name, version):
    result = executeCli(f"lib install {name}@{version}")
    return result

def installLibraryZip(zipPath):
    pass
    #TODO install from zip

#TODO add library gui for zip install

