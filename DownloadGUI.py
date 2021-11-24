from tkinter import Tk, Label
import time

base = "Deneyap Kart core ve kütüphaneleri indirliyor. bu işlem biraz zaman alabilir"
lbl = ""
window = ""

def startGUI() -> None:
    global lbl
    global window

    window = Tk()
    window.iconbitmap('icon.ico')
    window.title("Deneyap Kart Web")
    window.geometry("700x80")
    lbl = Label(window, text=base, font=("Arial", 15))

    lbl.pack(pady = 20, padx=10, anchor="w")
    window.after(1, animateText)
    window.mainloop()

def animateText() -> None:
    i = 0
    while True:
        i+=1
        text = base + "." *(i%4)
        lbl.config(text = text)
        window.update()
        time.sleep(0.5)

if __name__ == '__main__':
    startGUI()