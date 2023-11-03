import os
import numpy as np
from datetime import date
from datetime import datetime
import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass
from tkcalendar import DateEntry


@dataclass
class Record:
    created_at: (str, datetime)
    id: int
    state: str
    action: str

    def __post_init__(self):
        self.created_at = datetime.strptime(self.created_at, "%Y-%m-%d")


@dataclass
class Culture(Record):
    mushroom: str
    medium: str

    def __str__(self):
        return f"{self.created_at.strftime('%Y%m%d')}C{str(self.id).rjust(3, '0')}"


@dataclass
class Bag(Record):
    starter: str
    total_yield: float

    def __str__(self):
        return f"{self.created_at.strftime('%Y%m%d')}B{str(self.id).rjust(3, '0')}"


@dataclass
class GrainSpawn(Record):
    container: int

    def __str__(self):
        return f"{self.created_at.strftime('%Y%m%d')}GS{str(self.id).rjust(3, '0')}"


APP_NAME = "PyLabBook"


def create_popup(parent):
    # get main window position
    root_x = parent.winfo_rootx()
    root_y = parent.winfo_rooty()

    # add offset
    win_x = root_x + 300
    win_y = root_y + 100
    win = tk.Toplevel()
    win.geometry(f'+{win_x}+{win_y}')
    return win


class CreatePanel(tk.Frame):
    def __init__(self, parent):
        self.buttons = {
            "Bag": {"row": 0, "col": 0, "command": self.create_bag},
            "Grain Spawn": {"row": 0, "col": 1, "command": self.create_grain_spawn},
            "Culture": {"row": 1, "col": 0, "command": self.create_culture},
            "Recipe": {"row": 1, "col": 1, "command": self.create_recipe}
        }

        self.parent = parent

        tk.Frame.__init__(self, self.parent)
        self.frame = ttk.Frame(self.parent)
        self.label_frame = ttk.LabelFrame(self.frame, text="Create New")
        self.populate()
        self.label_frame.grid(row=0, column=0, sticky="nesw", padx=(20, 5), pady=(20, 5))
        self.frame.grid(row=0, column=0, sticky="nesw")

    def populate(self):
        for text, instructions in self.buttons.items():
            button = ttk.Button(self.label_frame, text=text, command=instructions["command"])
            button.grid(row=instructions["row"], column=instructions["col"], padx=(5, 5), pady=(5, 5))

    def create_bag(self, *args, **kwargs):
        popup = create_popup(self.parent)
        popup.wm_title("Window")

        label_frame = ttk.LabelFrame(popup, text="Create New Bag")
        label_frame.grid(row=0, column=0)

        created_at_label = ttk.Label(label_frame, text="Created at:")
        created_at_label.grid(row=1, column=0)

        created_at_var = tk.StringVar(label_frame, value=date.today().strftime("%Y-%m-%d"))
        created_at_widget = DateEntry(label_frame, date_pattern='y-mm-dd',
                                      textvariable=created_at_var)
        created_at_widget.grid(row=1, column=1)

        def foo():
            print(created_at_var.get())
            popup.destroy()

        b = ttk.Button(popup, text="Okay", command=foo)
        b.grid(row=2, column=0, columnspan=2)


    def create_grain_spawn(*args, **kwargs):
        # todo: implement me!
        raise NotImplementedError

    def create_culture(*args, **kwargs):
        # todo: implement me!
        raise NotImplementedError

    def create_recipe(*args, **kwargs):
        # todo: implement me!
        raise NotImplementedError


class InspectPanel(tk.Frame):
    def __init__(self, parent, title, row, column):
        self.entries = []
        tk.Frame.__init__(self, parent)
        self.content = ttk.Frame(parent)
        self.label_frame = ttk.LabelFrame(self.content, text=title)
        self.label_frame.grid(row=0, column=0, pady=(20, 5), padx=20, sticky="w")
        self.canvas = tk.Canvas(self.label_frame, borderwidth=0, width=530, scrollregion=(-492, 4, 4, 1270))

        self.frame = tk.Frame(self.canvas)
        self.vsb = tk.Scrollbar(self.label_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="right", fill="both", expand=True)
        self.canvas.create_window((4, 4), window=self.frame, anchor="ne", tags="self.frame")

        self.populate()
        self.frame.bind("<Configure>", self.on_frame_configure)

        self.sub_frame = ttk.Frame(self.content)
        self.confirm_button = ttk.Button(self.sub_frame, text="Confirm", command=self.confirm)
        self.confirm_button.grid(row=0, column=0, padx=5)
        self.reset_button = ttk.Button(self.sub_frame, text="Reset", command=self.reset)
        self.reset_button.grid(row=0, column=1, padx=5)
        self.mark_all_ok_button = ttk.Button(self.sub_frame, text="Mark all Ok", command=self.mark_all_ok)
        self.mark_all_ok_button.grid(row=0, column=2, padx=5)
        self.sub_frame.grid(row=1, column=0)
        self.content.grid(row=row, column=column, sticky="nesw", padx=5)

    def populate(self):
        raise NotImplementedError

    def confirm(self):
        raise NotImplementedError

    def reset(self):
        raise NotImplementedError

    def get_entries(self):
        raise NotImplementedError

    def mark_all_ok(self):
        for entry in self.entries:
            entry["status_var"].set(1)

    def on_frame_configure(self, event):
        """Reset the scroll region to encompass the inner frame"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


class InspectBagPanel(InspectPanel):
    def __init__(self, parent, title, row=0, column=1):
        super().__init__(parent, title, row, column)

    def initialize_bags(self):
        out = []
        for i in range(1, 40):
            rec = Bag("2023-10-01", i, "OK", "", f"20230901GS0{str(i % 3 + 1).rjust(3, '0')}", np.nan)
            bag = {"status_var": tk.BooleanVar(self.frame),
                   "action_var": tk.StringVar(self.frame),
                   "yield_var": tk.StringVar(self.frame, value=""),
                   "record": rec}
            out.append(bag)
        return out

    def populate(self):
        self.entries = self.initialize_bags()

        for i, text in enumerate(["Bag", "Passed", "Action", "Yield"]):
            header = ttk.Label(self.frame, text=text)
            header.grid(row=0, column=i)

        for i, _ in enumerate(self.entries, 1):
            bag_name = ttk.Label(self.frame, text=str(self.entries[i - 1]["record"]))
            bag_name.grid(row=i, column=0, padx=5)
            check_box = ttk.Checkbutton(self.frame,
                                        variable=self.entries[i - 1]["status_var"])
            check_box.grid(row=i, column=1)
            action_selection = ttk.Combobox(self.frame,
                                            textvariable=self.entries[i - 1]["action_var"],
                                            values=["", "Destroyed", "Induced Pinning", "Harvested"])
            action_selection.grid(row=i, column=2, padx=5)
            yield_entry = ttk.Entry(self.frame,
                                    textvariable=self.entries[i - 1]["yield_var"])
            yield_entry.grid(row=i, column=3, padx=5)

    def get_entries(self):
        out = []
        for entry in self.entries:
            record = entry["record"]
            bag = Bag(record.created_at.strftime("%Y-%m-%d"),
                      record.id,
                      "OK" if entry["status_var"].get() else "NOK",
                      entry["action_var"].get(),
                      record.starter,
                      float(entry["yield_var"].get()) if entry["yield_var"].get() else None)
            out.append(bag)

    def reset(self):
        for entry in self.entries:
            entry["status_var"].set(False)
            entry["action_var"].set("")
            entry["yield_var"].set("")


class InspectGrainSpawnPanel(InspectPanel):
    def __init__(self, parent, title, row=0, column=1):
        super().__init__(parent, title, row, column)

    def populate(self):
        self.entries = self.initialize_grain_spawn()
        for i, text in enumerate(["Grain Spawn", "Container", "Passed", "Action"]):
            header = ttk.Label(self.frame, text=text)
            header.grid(row=0, column=i)

        for i, entry in enumerate(self.entries, 1):
            gs_name = ttk.Label(self.frame,
                                text=str(self.entries[i-1]["record"]))
            gs_name.grid(row=i, column=0, padx=5)
            gs_container = ttk.Label(self.frame,
                                     text=self.entries[i-1]["record"].container)
            gs_container.grid(row=i, column=1, padx=5)
            check_box = ttk.Checkbutton(self.frame,
                                        variable=self.entries[i-1]["status_var"])
            check_box.grid(row=i, column=2)
            action_selection = ttk.Combobox(self.frame,
                                            values=["", "Destroyed", "Used"],
                                            textvariable=self.entries[i-1]["action_var"])
            action_selection.grid(row=i, column=3, padx=5)

    def reset(self):
        for entry in self.entries:
            entry["status_var"].set(False)
            entry["action_var"].set("")

    def mark_all_ok(self):
        for entry in self.entries:
            entry["status_var"].set(True)

    def initialize_grain_spawn(self):
        out = []
        for i in range(1, 40):
            rec = GrainSpawn("2023-10-01", i, "OK", "", i)
            gs = {"status_var": tk.BooleanVar(self.frame),
                  "action_var": tk.StringVar(self.frame),
                  "record": rec}
            out.append(gs)
        return out


class InspectCulturePanel(InspectPanel):
    def __init__(self, parent, title, row=0, column=1):
        super().__init__(parent, title, row, column)

    def initialize_cultures(self):
        out = []
        for i in range(1, 5):
            rec = Culture("2023-10-01", i, "", "", np.random.choice(["Lions Mane", "Oyster Mushroom"]), "Agar")
            cul = {"status_var": tk.BooleanVar(self.frame, value=True),
                   "record": rec}
            out.append(cul)
        return out

    def populate(self):
        self.entries = self.initialize_cultures()
        for i, text in enumerate(["Culture", "Mushroom", "Medium", "Passed"]):
            header = ttk.Label(self.frame, text=text)
            header.grid(row=0, column=i)

        for i, _ in enumerate(self.entries, 1):
            cul_name = ttk.Label(self.frame, text=str(self.entries[i-1]["record"]))
            cul_name.grid(row=i, column=0, padx=5)
            cul_mushroom = ttk.Label(self.frame, text=self.entries[i-1]["record"].mushroom)
            cul_mushroom.grid(row=i, column=1, padx=5)
            cul_medium = ttk.Label(self.frame, text=self.entries[i-1]["record"].medium)
            cul_medium.grid(row=i, column=2, padx=5)
            check_box = ttk.Checkbutton(self.frame, variable=self.entries[i-1]["status_var"])
            check_box.grid(row=i, column=3)


class App(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.title(APP_NAME)
        self._set_style()

        self.content = ttk.Frame(self)

        create_panel = CreatePanel(self.content)

        inspect_culture_panel = InspectCulturePanel(self.content, "Inspect Cultures",
                                                    row=1, column=1)

        inspect_grain_spawn_panel = InspectGrainSpawnPanel(self.content, "Inspect Grain Spawn",
                                                           row=1, column=0)
        inspect_bag_panel = InspectBagPanel(self.content, "Inspect Bags",
                                            row=0, column=1)

        create_panel.grid(row=0, column=0, sticky="nesw")
        inspect_culture_panel.grid(row=1, column=1, sticky="w")
        inspect_grain_spawn_panel.grid(row=1, column=0, sticky="w")
        inspect_bag_panel.grid(row=0, column=1, sticky="w")
        self.content.pack(expand=True, fill="both")

    def _set_style(self):
        self.style = ttk.Style(self)
        # Import the tcl file
        self.tk.call("source", os.path.join("styles", "forest-dark.tcl"))
        # Set the theme with the theme_use method
        self.style.theme_use("forest-dark")

    def _make_responsive(self):
        self.option_add("*tearOff", False)
        self.columnconfigure(index=0, weight=1)
        self.columnconfigure(index=1, weight=1)
        self.columnconfigure(index=2, weight=1)
        self.rowconfigure(index=0, weight=1)
        self.rowconfigure(index=1, weight=1)
        self.rowconfigure(index=2, weight=1)


if __name__ == "__main__":
    app = App()
    app.mainloop()