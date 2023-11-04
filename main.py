import os
import random
import tkinter as tk
from tkinter import ttk
from datetime import date
from tkcalendar import DateEntry

from datastructures import Bag, Culture, GrainSpawn


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
    def __init__(self, parent, padx=(20, 5), pady=(20, 5)):
        super().__init__(parent)

        self.buttons = {
            "Bag": {"row": 0, "col": 0, "command": self.create_bag},
            "Grain Spawn": {"row": 0, "col": 1, "command": self.create_grain_spawn},
            "Culture": {"row": 1, "col": 0, "command": self.create_culture},
            "Recipe": {"row": 1, "col": 1, "command": self.create_recipe}
        }

        self.parent = parent

        self.frame = ttk.Frame(self.parent)
        self.label_frame = ttk.LabelFrame(self.frame, text="Create New")
        self.populate()
        self.label_frame.grid(row=0, column=0, sticky="nesw", padx=padx, pady=pady)
        self.frame.grid(row=0, column=0, sticky="nesw")

    def populate(self):
        for text, instructions in self.buttons.items():
            button = ttk.Button(self.label_frame, text=text, command=instructions["command"])
            button.grid(row=instructions["row"], column=instructions["col"], padx=5, pady=5)

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
    def __init__(self, parent, title, width=None):
        super().__init__(parent)
        self.entries = []

        self.label_frame = ttk.LabelFrame(self, text=title, width=width)
        self.label_frame.grid(row=0, column=0, pady=(20, 5), padx=20, sticky="news")
        self.label_frame.grid_columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(self.label_frame, borderwidth=0)

        self.frame = tk.Frame(self.canvas)
        self.vsb = tk.Scrollbar(self.label_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="right", fill="both", expand=True)
        self.canvas.create_window((4, 4), window=self.frame, anchor="ne", tags="self.frame")

        self.populate()
        self.frame.bind("<Configure>", self.on_frame_configure)

        self.sub_frame = ttk.Frame(self)
        self.confirm_button = ttk.Button(self.sub_frame, text="Confirm", command=self.confirm)
        self.confirm_button.grid(row=0, column=0, padx=5)
        self.reset_button = ttk.Button(self.sub_frame, text="Reset", command=self.reset)
        self.reset_button.grid(row=0, column=1, padx=5)
        self.mark_all_ok_button = ttk.Button(self.sub_frame, text="Mark all Ok", command=self.mark_all_ok)
        self.mark_all_ok_button.grid(row=0, column=2, padx=5)
        self.sub_frame.grid(row=1, column=0)
        self.grid(row=0, column=0, sticky="nesw", padx=5)

        self.grid_columnconfigure(0, weight=1)


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

    def _place_label(self, text, row, column, padx=0):
        label = ttk.Label(self.frame, text=text)
        label.grid(row=row, column=column, padx=padx)

    def _place_checkbox(self, variable, idx, column, padx=0):
        check = ttk.Checkbutton(self.frame, variable=variable)
        check.grid(row=idx, column=column, padx=padx)

    def _place_selection(self, values, variable, idx, column, padx=0):
        select = ttk.Combobox(self.frame, values=values, textvariable=variable)
        select.grid(row=idx, column=column, padx=padx)

    def _place_entry(self, variable, idx, column, padx=0):
        entry = ttk.Entry(self.frame, textvariable=variable)
        entry.grid(row=idx, column=column, padx=padx)


class InspectBagPanel(InspectPanel):
    def __init__(self, parent, title, width=None):
        super().__init__(parent, title, width)

    def initialize_bags(self):
        out = []
        for i in range(1, 40):
            rec = Bag("2023-10-01", i, "OK", "", "Lion's Mane", f"20230901GS0{str(i % 3 + 1).rjust(3, '0')}", None)
            bag = {"status_var": tk.BooleanVar(self.frame),
                   "action_var": tk.StringVar(self.frame),
                   "yield_var": tk.StringVar(self.frame, value=""),
                   "record": rec}
            out.append(bag)
        return out

    def populate(self):
        self.entries = self.initialize_bags()
        columns = ["Bag", "Starter", "Mushroom", "Passed", "Action", "Yield"]
        for i, text in enumerate(columns):
            header = ttk.Label(self.frame, text=text)
            header.grid(row=0, column=i)
            self.frame.grid_columnconfigure(i, weight=1)

        for i, entry in enumerate(self.entries, 1):
            self._populate_row(entry, i)

    def _populate_row(self, entry, idx):
        record = entry["record"]
        self._place_label(str(record), idx, 0, 5)
        self._place_label(record.starter, idx, 1, 5)
        self._place_label(record.mushroom, idx, 2, 5)
        self._place_checkbox(entry["status_var"], idx, 3, 5)
        self._place_selection(["", "Induced Pinning", "Harvested", "Destroyed"], entry["action_var"], idx, 4, 5)
        self._place_entry(entry["yield_var"], idx, 5, 5)

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
    def __init__(self, parent, title, width=None):
        super().__init__(parent, title, width)

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
    def __init__(self, parent, title, width=None):
        super().__init__(parent, title, width)

    def initialize_cultures(self):
        out = []
        for i in range(1, 5):
            rec = Culture("2023-10-01", i, "", "", random.choice(["Lions Mane", "Oyster Mushroom"]), "Agar")
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


class LabTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        create_panel = CreatePanel(self, padx=(20, 5), pady=(20, 5))
        notebook = ttk.Notebook(self)

        inspect_bag_panel = InspectBagPanel(notebook, "Inspect Bags", width=1000)
        inspect_grain_spawn_panel = InspectGrainSpawnPanel(notebook, "Inspect Grain Spawn", width=1000)
        inspect_culture_panel = InspectCulturePanel(notebook, "Inspect Cultures")

        for tab, lab in zip([inspect_bag_panel, inspect_grain_spawn_panel, inspect_culture_panel],
                            ["Bags", "Grain Spawn", "Cultures"]):
            notebook.add(tab, text=lab)

        create_panel.grid(row=0, column=1, sticky="news")
        notebook.grid(row=0, column=1, sticky="news")

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=5)


class FinanceTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)


class HistoryTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)


class App(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self._set_style()
        self.title("PyLabBook")

        notebook = ttk.Notebook(self)
        lab_tab = LabTab(notebook)
        lab_tab.pack(fill="both", expand=True)
        history_tab = HistoryTab(notebook)
        history_tab.pack(fill="both", expand=True)
        finance_tab = FinanceTab(notebook)
        finance_tab.pack(fill="both", expand=True)

        for tab, lab in zip([lab_tab, history_tab, finance_tab], ["Lab", "History", "Finances"]):
            notebook.add(tab, text=lab)

        notebook.pack(expand=True, fill='both')

    def _set_style(self):
        self.style = ttk.Style(self)
        # Import the tcl file
        self.tk.call("source", os.path.join("styles", "forest-dark.tcl"))
        # Set the theme with the theme_use method
        self.style.theme_use("forest-dark")


if __name__ == "__main__":
    app = App()
    # app.state("zoomed")
    app.mainloop()