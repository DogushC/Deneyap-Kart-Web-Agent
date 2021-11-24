from tkinter import Tk
from tkinter.messagebox import showerror




def showError(message:str) -> None:
    root = Tk()
    root.withdraw()
    showerror(title = "Hata", message = message)
    root.destroy()