from tkinter import Tk, Label




def startGUI():
    window = Tk()
    window.iconbitmap('icon.ico')
    window.title("Deneyap Kart Web")

    lbl = Label(window, text="Deneyap Kart core ve kütüphaneleri indirliyor... bu işlem biraz zaman alabilir.", font=("Arial", 15))

    lbl.pack(pady = 20, padx=10)

    window.mainloop()




if __name__ == '__main__':
    startGUI()