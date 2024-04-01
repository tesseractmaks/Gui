import asyncio
import functools
import os
import tkinter

from tkinter import messagebox, ttk
from dotenv import load_dotenv
from sender import register


def click_register(entries, root, host, port):
    nickname = entries["username"].get()
    if not nickname:
        messagebox.showerror("Error", "Username can't be blank")
        return

    asyncio.run(register(nickname, host, port))
    messagebox.showinfo("Info", "Credential saved to credentials.json")

    root.quit()


def set_entry(label_text, default=""):
    frame = ttk.Frame(borderwidth=0, relief=tkinter.SOLID, padding=[8, 10])

    label = ttk.Label(frame, text=label_text)
    label.pack(anchor=tkinter.NW)

    entry = ttk.Entry(frame)
    entry.pack(anchor=tkinter.NW, expand=True, fill=tkinter.X)
    entry.insert(0, default)

    frame.pack(anchor=tkinter.NW, fill=tkinter.X, padx=5, pady=5)
    return entry


def main():
    host = str(os.getenv("HOST"))
    port = str(os.getenv("PORT_WRITE"))
    root = tkinter.Tk()
    root.title("Registration to the chat")
    root.geometry("300x150+300+300")

    entries = {"username": set_entry("Username:")}

    click_handler = functools.partial(
        click_register,
        entries=entries,
        root=root,
        host=host,
        port=port
    )
    btn = ttk.Button(text="Press to register", command=click_handler)
    btn.pack(side=tkinter.BOTTOM, fill=tkinter.X)
    root.mainloop()


if __name__ == "__main__":
    load_dotenv()
    main()
