from tkinter import Tk
from tkinter.messagebox import showerror




def showError(message):
    root = Tk()
    root.withdraw()
    showerror(title = "Hata", message = message)
    root.destroy()