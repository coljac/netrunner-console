import tkinter as tk
import queue
from PIL import ImageTk, Image
import os
import sys
from threading import Thread

image_location = "/home/coljac/build/cards"
windows = []

def show_image_window(card="00001", geometry=None):
    t = Thread(target=_show_image_window, args=([card, geometry])) 
    t.start()

def _show_image_window(card, geometry):
    if is_image_window():
        close_image_window()

    window = tk.Tk()
    windows.append(window)
    
    if geometry is None:
        # 300x419
        width = 300 + 10  # width for the Tk root
        height = 419 + 10 # height for the Tk root
        # get screen width and height
        ws = window.winfo_screenwidth()  # width of the screen
        hs = window.winfo_screenheight()  # height of the screen

        # calculate x and y coordinates for the Tk root window
        x = (ws / 2) - (width / 2)
        y = (hs / 2) - (height / 2)

        # set the dimensions of the screen
        # and where it is placed
        geometry = '%dx%d+%d+%d' % (width, height, x, y)

    window.title("Card")
    window.geometry(geometry)
    window.configure(background='white')

    image_file = image_location + "/" + card + ".png"
    try:
        img = ImageTk.PhotoImage(Image.open(image_file))
        w = tk.Label(window, image=img)
    except IOError:
        w = tk.Label(window, image=None)
    windows.append(w)
    
    w.pack(side="bottom", fill="both", expand="yes")

    window.mainloop()


def update_image_window(card="00001"):
    w = windows[1]
    image_file = image_location + "/" + card + ".png"
    try:
        img = ImageTk.PhotoImage(Image.open(image_file))
    except IOError:
        return
    w.configure(image=img)
    windows.append(img)
    # sys.stderr.write(windows[0].geometry)


def close_image_window():
    geometry = None 
    if len(windows) > 0:
        geometry = windows[0].winfo_geometry()
        windows[0].quit()
        windows[0].destroy()
        windows.clear()
    return geometry
        


def is_image_window():
    return len(windows) > 0


