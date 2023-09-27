import tkinter
import tkinter.filedialog
import tkinter.simpledialog
import subprocess
import json

from tkinter.scrolledtext import ScrolledText
from tkinter.ttk import Treeview
from PIL import ImageTk, Image
from threading import Thread
from os import environ
from os.path import isfile
from shutil import copyfile

_query = 0
_query_proc = []
_is_filename_in_config = False


# Create settings on first initialization.
if not isfile("settings.json"):
    copyfile("defaultsettings.json", "settings.json")


class Redirect:
    def __init__(self, widget, autoscroll=True):
        self.widget = widget
        self.autoscroll = autoscroll

    def write(self, textbox):
        self.widget.insert('end', textbox)
        if self.autoscroll:
            self.widget.see('end')

    def flush(self):
        pass


def center_window(win):
    """
    Centers a Tkinter window.
    :param win: The main window or Toplevel window to center.
    """
    win.attributes('-alpha', 0.0)
    win.update_idletasks()
    width = win.winfo_width()
    frm_width = win.winfo_rootx() - win.winfo_x()
    win_width = width + 2 * frm_width
    height = win.winfo_height()
    titlebar_height = win.winfo_rooty() - win.winfo_y()
    win_height = height + titlebar_height + frm_width
    x = win.winfo_screenwidth() // 2 - win_width // 2
    y = win.winfo_screenheight() // 2 - win_height // 2
    win.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    win.deiconify()
    win.attributes('-alpha', 1.0)


def get_settings():
    with open("settings.json") as sf:
        return json.load(sf)


def regular(size):
    return "Segoe UI Semibold", size


def textbox_control(query_no, text: tkinter.Text):
    global _query_proc
    while query_no not in _query_proc:
        pass
    text.delete("1.0", "end")
    return "break"


def download(query_no, text: tkinter.Text, path: str, scrollbox, output_f: str):
    global _query_proc
    query = text.get("1.0", "end-1c")
    _query_proc.append(query_no)
    try:
        process = subprocess.check_output(f"spotdl download \"{query}\" --format mp3 --output \"{path}\\{output_f}")
    except subprocess.CalledProcessError:
        scrollbox.configure(state="normal")
        scrollbox.insert(tkinter.INSERT, "\nInvalid query.")
        scrollbox.configure(state="disabled")
        scrollbox.see(tkinter.END)
    else:
        res_text = \
            "".join(str(process).split("\\r\\n")[2:]).replace("\\", "").replace("  ", "").\
            replace(":h", ": h").replace("xe2x80x99", "'").replace("music.youtube.com", "youtu.be").\
            replace("Downloaded \"", "\nDownloaded \"")
        if res_text.startswith(" Found "):
            res_text = "\n" + res_text[1:]
        if res_text.endswith("\'"):
            res_text = res_text[:len(res_text)-1]
        scrollbox.configure(state="normal")
        scrollbox.insert(
            tkinter.INSERT,
            res_text
        )
        scrollbox.configure(state="disabled")
        scrollbox.see(tkinter.END)
        _query_proc.remove(query_no)


def download_procedure(text: tkinter.Text, path: str, scrollbox: ScrolledText):
    global _query
    _query += 1
    scrollbox.configure(state="normal")
    scrollbox.insert(
        tkinter.INSERT, ("\n" if _query > 1 else "") + f"Processing query \"{text.get('1.0', 'end-1c')}\"..."
    )
    scrollbox.configure(state="disabled")
    scrollbox.see(tkinter.END)
    Thread(target=lambda: textbox_control(_query, text)).start()
    Thread(target=lambda: download(_query, text, path, scrollbox, get_settings()["filename_format"])).start()


window = tkinter.Tk()
window.title("Spotify Downloader")
window.geometry("1000x600")
window.maxsize(width=1000, height=600)
window.minsize(width=1000, height=600)
center_window(window)

title_image_frame = tkinter.Frame(window, width=236, height=71)
title_image_frame.pack()
title_image_frame.place(anchor="n", relx=0.5)
title_image_pillow = ImageTk.PhotoImage(Image.open("titleimage.png"))
title = tkinter.Label(title_image_frame, image=title_image_pillow)
title.pack()

link = tkinter.Text(window, bd=0.5, font=regular(10), width=100, height=1,
                    relief="solid", spacing1=5, spacing2=0, spacing3=5, padx=10, wrap="none")
link.pack()
link.place(relx=0.5, rely=0.23, anchor="center")
link.bind(
    "<Return>", lambda event: download_procedure(link, get_settings()["save_location"].replace("/", "\\"), resultbox)
)
link_hint = tkinter.Label(window, text="Paste the URL of a spotify song, playlist, album, or an artist. You can also "
                                       "search by typing your query above. Hit <Enter> to download.", font=regular(10))
link_hint.place(relx=0.5, rely=0.3, anchor="center")

resultbox = ScrolledText(
    window, wrap="none", spacing1=5, spacing3=5, padx=10, font=regular(8), width=100,
    height=6, relief="solid", bd=0
)
resultbox.pack()
resultbox.place(relx=0.5, rely=0.46, anchor="center")
resultbox.insert(tkinter.INSERT, "⚠︎ Console, used for viewing download statuses. This box is read-only.\n")
resultbox.configure(state="disabled")


def browse_directory_cb():
    settings = get_settings()
    new_dir = tkinter.filedialog.askdirectory()
    if new_dir == "":
        return
    settings["save_location"] = new_dir
    with open("settings.json", "w") as sf:
        json.dump(settings, sf)


def open_directory_cb():
    _path = get_settings()['save_location'].replace('/', '\\').replace("%userprofile%", environ["USERPROFILE"])
    subprocess.Popen("explorer.exe " + f"\"{_path}\"")


def inputbox_validate_procedure(textbox: tkinter.Text, _window):
    new_sf = get_settings()
    new_sf["filename_format"] = textbox.get("1.0", "end-1c")
    with open("settings.json", "w") as sf:
        json.dump(new_sf, sf)
    _window.destroy()


def inputbox_cancel_procedure(_window):
    _window.destroy()
    return "break"


def filename_bcb():
    new_window = tkinter.Toplevel(window)
    new_window.title("Change filename format...")
    new_window.geometry("900x450")
    center_window(new_window)

    table = Treeview(new_window)
    table["columns"] = ("a", "b", "c", "d", "e", "f")
    table.column("#0", width=0, stretch=False)
    table.column("a", anchor="center", width=85)
    table.column("b", anchor="center", width=140)
    table.column("c", anchor="center", width=115)
    table.column("d", anchor="center", width=110)
    table.column("e", anchor="center", width=220)
    table.column("f", anchor="center", width=145)
    table.heading("a", text="Variable")
    table.heading("b", text="Description")
    table.heading("c", text="Example")
    table.heading("d", text="Variable")
    table.heading("e", text="Description")
    table.heading("f", text="Example")
    table.insert(
        parent="", index="end", iid="0", text="",
        values=("{title}", "Song title", "Dark Horse", "{original-date}", "Date of original release", "2013-01-01")
    )
    table.insert(
        parent="", index="end", iid="1", text="",
        values=("{artists}", "Song artists", "Katy Perry, Juicy J", "{track-number}", "Track number in the album", "06")
    )
    table.insert(
        parent="", index="end", iid="2", text="",
        values=("{artist}", "Primary artist", "Katy Perry", "{tracks-count}", "Track count in the album", "13")
    )

    table.insert(
        parent="", index="end", iid="3", text="",
        values=("{album}", "Album name", "PRISM", "{isrc}", "International Standard Recording Code", "USUM71311296")
    )
    table.insert(
        parent="", index="end", iid="4", text="",
        values=(
            "{album-artist}", "Album primary artist", "Katy Perry", "{track-id}", "Spotify Song ID",
            "4jbmgIyjGoXjY01XxatOx6"
        )
    )
    table.insert(
        parent="", index="end", iid="5", text="",
        values=("{genre}", "Genre", "dance pop", "{publisher}", "Record label", "Capitol Record (CAP)")
    )
    table.insert(
        parent="", index="end", iid="6", text="",
        values=("{disc-number}", "Disc number", "1", "{list-length}", "Number of items in a playlist", "10")
    )
    table.insert(
        parent="", index="end", iid="7", text="",
        values=("{disc-count}", "Total disc count", "2", "{list-position}", "Position of song in a playlist", "5")
    )
    table.insert(
        parent="", index="end", iid="8", text="",
        values=("{duration}", "Song duration (seconds)", "215.672", "{list-name}", "Playlist name", "Saved")
    )
    table.insert(
        parent="", index="end", iid="9", text="",
        values=("{year}", "Year of release", "2013", "{output-ext}", "File extension", "mp3")
    )
    table.pack()

    description = tkinter.Label(
        new_window,
        text="Use the above tags to reformat the filename. e.g. {title} will be replaced by \"Enchanted\". Hit <Enter> "
             "to validate and <Esc> to cancel.",
        font=regular(9)
    )
    description.pack()
    description.place(relx=0.5, rely=0.55, anchor="center")

    inputbox = tkinter.Text(new_window, bd=0.5, font=regular(10), width=100, height=1, relief="solid", spacing1=5,
                            spacing2=0, spacing3=5, padx=10, wrap="none")
    inputbox.pack()
    inputbox.place(relx=0.5, rely=0.62, anchor="center")
    inputbox.bind("<Return>", lambda event: inputbox_validate_procedure(inputbox, new_window))
    inputbox.bind("<Escape>", lambda event: inputbox_cancel_procedure(new_window))
    inputbox.insert(tkinter.INSERT, get_settings()["filename_format"])


directory_browse = tkinter.Button(
    window, text="Choose save directory...", relief="solid", command=browse_directory_cb, width=25, bd=0.5
)
directory_browse.pack()
directory_browse.place(relx=0.3, rely=0.62, anchor="center")
directory_open = tkinter.Button(
    window, text="Open save directory...", relief="solid", command=open_directory_cb, width=25, bd=0.5
)
directory_open.pack()
directory_open.place(relx=0.5, rely=0.62, anchor="center")

filename_b = tkinter.Button(
    window, text="Change filename formatting...", relief="solid", command=filename_bcb, width=25, bd=0.5
)
filename_b.pack()
filename_b.place(relx=0.7, rely=0.62, anchor="center")

window.mainloop()
