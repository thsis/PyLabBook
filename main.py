import os
import random
import sqlite3
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from datetime import date
from tkcalendar import DateEntry

from datastructures import Recipe, Bag, Culture, GrainSpawn
from database import Database


def _create_popup(parent):
    # get main window position
    root_x = parent.winfo_rootx()
    root_y = parent.winfo_rooty()

    # add offset
    win_x = root_x + 300
    win_y = root_y + 100
    win = tk.Toplevel(parent)
    win.geometry(f'+{win_x}+{win_y}')
    return win


def _place_label(parent, text, row, column, **kwargs):
    label = ttk.Label(parent, text=text)
    label.grid(row=row, column=column, **kwargs)
    return label


def _place_checkbox(parent, variable, row, column, **kwargs):
    check = ttk.Checkbutton(parent, variable=variable)
    check.grid(row=row, column=column, **kwargs)
    return check


def _place_selection(parent, values, variable, row, column, command=None, **kwargs):
    select = ttk.Combobox(parent, values=values, textvariable=variable, postcommand=command)
    select.grid(row=row, column=column, **kwargs)
    return select


def _place_entry(parent, variable, row, column, **kwargs):
    entry = ttk.Entry(parent, textvariable=variable)
    entry.grid(row=row, column=column, **kwargs)
    return entry


def _place_labelframe(parent, text, row, column, **kwargs):
    label_frame = ttk.LabelFrame(parent, text=text)
    label_frame.grid(row=row, column=column, **kwargs)
    return label_frame


def _place_button(parent, text, command, row, column, **kwargs):
    button = ttk.Button(parent, text=text, command=command)
    button.grid(row=row, column=column, **kwargs)
    return button


def _place_text(parent, row, column, width=1, height=20, disable=False, **kwargs):
    text = tk.Text(parent, width=width, height=height)
    text.grid(row=row, column=column, **kwargs)
    if disable:
        text.config(state=tk.DISABLED)
    return text


def _place_counter(parent, variable, row, column, width=None, **kwargs):
    counter = ttk.Spinbox(parent, width=width, textvariable=variable)
    counter.grid(row=row, column=column, **kwargs)
    return counter


class CreatePanel(tk.Frame):
    def __init__(self, parent, database, padx=None, pady=None):
        super().__init__(parent)
        self.database = database

        self.buttons = {
            "Bag": self.create_bag,
            "Grain Spawn": self.create_grain_spawn,
            "Culture": self.create_culture,
            "Recipe": self.create_recipe
        }

        self.parent = parent

        self.frame = ttk.Frame(self.parent)

        self.date_label = ttk.LabelFrame(self.frame, text="Date")
        self.date_label.grid(row=0, column=0, sticky="news", padx=padx, pady=pady)
        self.created_at_var = tk.StringVar(self.frame, value=date.today().strftime("%Y-%m-%d"))
        self.created_at_widget = DateEntry(self.date_label, date_pattern='y-mm-dd', textvariable=self.created_at_var)
        self.created_at_widget.grid(row=0, column=0, sticky="news", padx=padx, pady=pady)

        self.label_frame = ttk.LabelFrame(self.frame, text="Create New")
        self.populate()
        self.label_frame.grid(row=1, column=0, sticky="nesw", padx=padx, pady=pady)
        self.frame.grid(row=0, column=0, sticky="nesw")

    def populate(self):
        for i, (text, command) in enumerate(self.buttons.items()):
            button = ttk.Button(self.label_frame, text=text, command=command)
            button.grid(row=i, column=0, padx=5, pady=5)

    def create_bag(self, *args, **kwargs):
        popup = _create_popup(self.parent)
        popup.wm_title("Create New Bag")

        label_frame = ttk.LabelFrame(popup, text="Create New Bag")
        label_frame.grid(row=0, column=0)

        created_at_label = ttk.Label(label_frame, text="Created at:")
        created_at_label.grid(row=1, column=0)

        created_at_var = tk.StringVar(label_frame, value=date.today().strftime("%Y-%m-%d"))
        created_at_widget = DateEntry(label_frame, date_pattern='y-mm-dd',
                                      textvariable=created_at_var)
        created_at_widget.grid(row=1, column=1)

        def foo():
            popup.destroy()

        b = ttk.Button(popup, text="Okay", command=foo)
        b.grid(row=2, column=0, columnspan=2)

    def create_grain_spawn(self, *args, **kwargs):
        # todo: implement me!
        raise NotImplementedError

    def get_next_culture_title(self, created_at):
        counter = self.database.get_n(table="cultures", created_at=created_at) + 1
        culture = Culture(created_at=created_at,
                          id=counter,
                          mushroom="",
                          variant="",
                          medium="")
        return str(culture)

    def create_culture(self, *args, **kwargs):
        def write_culture():
            nonlocal popup
            try:
                culture = Culture(id=self.database.get_n("cultures", created_at_var.get()) + 1,
                                  variant=variant_name.get(),
                                  created_at=created_at_var.get(),
                                  medium=medium_var.get(),
                                  mushroom=mushroom_var.get())

                self.database.write(culture)
                messagebox.showinfo("", "Culture was added to database.")
                popup.destroy()
            except (sqlite3.DatabaseError, sqlite3.IntegrityError) as e:
                messagebox.showerror("Error", e)
                raise e

        def update_recipe_panel(var, index, mode):
            selected = medium_var.get()
            if recipe := recipes.get(selected):
                ingredients_panel.config(state=tk.NORMAL)
                instructions_panel.config(state=tk.NORMAL)
                ingredients_panel.delete(1.0, tk.END)
                instructions_panel.delete(1.0, tk.END)
                ingredients_panel.insert(1.0, recipe.ingredients)
                instructions_panel.insert(1.0, recipe.instructions)
                ingredients_panel.config(state=tk.DISABLED)
                instructions_panel.config(state=tk.DISABLED)

        def update_culture_title(var, index, mode):
            created_at = created_at_var.get()
            if created_at:
                text = self.get_next_culture_title(created_at)
                title_label.config(text=text)

        popup = _create_popup(self.parent)
        popup.title("Add New Culture")
        # todo: configure column width
        popup.grid_columnconfigure(0, weight=1)
        popup.grid_columnconfigure(1, weight=3)

        variant_name = tk.StringVar()
        mushroom_var = tk.StringVar()
        medium_var = tk.StringVar()
        medium_var.trace_add("write", update_recipe_panel)
        created_at_var = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        created_at_var.trace_add("write", update_culture_title)

        mushrooms = self.database.get_unique_mushrooms()
        recipes = self.database.get_recipes("Growth Medium")

        control_panel = ttk.Frame(popup)
        control_panel.grid(row=0, column=0, sticky="nw")
        recipe_panel = ttk.Frame(popup)
        recipe_panel.grid(row=0, column=1, sticky="news")

        # todo: implement naming scheme
        title_label = _place_label(control_panel, "", row=0, column=0, columnspan=2)

        _place_label(control_panel, "Variant:", row=1, column=0, sticky="news")
        _place_entry(control_panel, variant_name, row=1, column=1, sticky="news")
        _place_label(control_panel, "Created At:", row=2, column=0, sticky="news")
        created_at_widget = DateEntry(control_panel, date_pattern='y-mm-dd', textvariable=created_at_var)
        created_at_widget.grid(row=2, column=1, sticky="news")

        _place_label(control_panel, "Mushroom:", row=3, column=0, sticky="news")
        _place_selection(control_panel, mushrooms, mushroom_var, row=3, column=1, sticky="news")
        _place_label(control_panel, "Medium:", row=4, column=0, sticky="news")
        _place_selection(control_panel, list(recipes.keys()), medium_var, row=4, column=1, sticky="news")
        _place_button(control_panel, "Okay", write_culture, row=5, column=0, columnspan=2)

        _place_label(recipe_panel, "Ingredients", row=0, column=0)
        ingredients_panel = _place_text(recipe_panel, row=1, column=0, width=70, height=10, disable=True)
        _place_label(recipe_panel, "Instructions", row=2, column=0)
        instructions_panel = _place_text(recipe_panel, row=3, column=0, width=70, disable=True)





    def create_recipe(self, *args, **kwargs):
        def write_recipe():
            nonlocal popup
            name = name_var.get()
            recipe_type = type_var.get()
            ingredients = ingredients_text.get("0.0", tk.END)
            instructions = instructions_text.get("0.0", tk.END)

            try:
                recipe = Recipe(name=name, recipe_type=recipe_type, ingredients=ingredients, instructions=instructions)
                self.database.write(recipe)
                messagebox.showinfo("", "Recipe was written to Database!")
                popup.destroy()
            except AssertionError:
                messagebox.showerror("Error", "Recipe Name, Ingredients or Instructions cannot be empty")
            except (sqlite3.DatabaseError, sqlite3.IntegrityError) as e:
                messagebox.showerror("Error", e)
                raise e

        popup = _create_popup(self.parent)
        popup.title("Create New Recipe")
        popup.grid_columnconfigure(0, weight=1, uniform="t")
        popup.grid_columnconfigure(1, weight=3, uniform="t")

        name_var = tk.StringVar()
        type_var = tk.StringVar()
        ingredients_text = _place_text(popup, width=15, row=3, column=0, sticky="news")
        instructions_text = _place_text(popup, width=50, row=3, column=1, sticky="news")

        _place_label(popup, "Recipe Name:", row=0, column=0, sticky="news")
        _place_entry(popup, variable=name_var, row=0, column=1, sticky="news")
        _place_label(popup, "Recipe Type:", row=1, column=0, sticky="news")
        _place_selection(popup, ('Growth Medium', 'Grain Spawn', 'Substrate'), type_var, row=1, column=1, sticky="news")
        _place_label(popup, "Ingredients", row=2, column=0, sticky="news")
        _place_label(popup, "Instructions", row=2, column=1, sticky="news")

        _place_button(popup, "Okay",
                      command=write_recipe,
                      row=4, column=0, columnspan=2)


class InspectPanel(tk.Frame):
    def __init__(self, parent, title, database, width=None):
        super().__init__(parent)
        self.database = database
        self.entries = []

        self.label_frame = ttk.LabelFrame(self, text=title, width=width)
        self.label_frame.grid(row=0, column=0, pady=(20, 5), padx=20, sticky="news")
        self.label_frame.grid_columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(self.label_frame, borderwidth=0, width=width)

        self.frame = tk.Frame(self.canvas, width=width)
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


class InspectBagPanel(InspectPanel):
    def __init__(self, parent, title, database, width=None):
        super().__init__(parent, title, database, width)

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
        pass
        # self.entries = self.initialize_bags()
        # columns = ["Bag", "Starter", "Mushroom", "Passed", "Action", "Yield"]
        # for i, text in enumerate(columns):
        #     header = ttk.Label(self.frame, text=text)
        #     header.grid(row=0, column=i)
        #     self.frame.grid_columnconfigure(i, weight=1)
#
        # for i, entry in enumerate(self.entries, 1):
        #     self._populate_row(entry, i)

    def _populate_row(self, entry, idx):
        record = entry["record"]
        _place_label(self.frame, str(record), idx, 0, padx=5)
        _place_label(self.frame, record.starter, idx, 1, padx=5)
        _place_label(self.frame, record.mushroom, idx, 2, padx=5)
        _place_checkbox(self.frame, entry["status_var"], idx, 3, padx=5)
        _place_selection(self.frame, ["", "Induced Pinning", "Harvested", "Destroyed"], entry["action_var"], idx, 4, padx=5)
        _place_entry(self.frame, entry["yield_var"], idx, 5, padx=5)

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
    def __init__(self, parent, title, database, width=None):
        super().__init__(parent, title, database, width)

    def populate(self):
        pass
        # self.entries = self.initialize_grain_spawn()
        # for i, text in enumerate(["Grain Spawn", "Container", "Passed", "Action"]):
        #     header = ttk.Label(self.frame, text=text)
        #     header.grid(row=0, column=i)
#
        # for i, entry in enumerate(self.entries, 1):
        #     gs_name = ttk.Label(self.frame,
        #                         text=str(self.entries[i-1]["record"]))
        #     gs_name.grid(row=i, column=0, padx=5)
        #     gs_container = ttk.Label(self.frame,
        #                              text=self.entries[i-1]["record"].container)
        #     gs_container.grid(row=i, column=1, padx=5)
        #     check_box = ttk.Checkbutton(self.frame,
        #                                 variable=self.entries[i-1]["status_var"])
        #     check_box.grid(row=i, column=2)
        #     action_selection = ttk.Combobox(self.frame,
        #                                     values=["", "Destroyed", "Used"],
        #                                     textvariable=self.entries[i-1]["action_var"])
        #     action_selection.grid(row=i, column=3, padx=5)

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
    def __init__(self, parent, title, database, width=None):
        super().__init__(parent, title, database, width)

    def initialize_cultures(self):
        out = []
        for i in range(1, 5):
            rec = Culture("2023-10-01", i, "", "", random.choice(["Lions Mane", "Oyster Mushroom"]), "Agar")
            cul = {"status_var": tk.BooleanVar(self.frame, value=True),
                   "record": rec}
            out.append(cul)
        return out

    def populate(self):
        pass
        # self.entries = self.initialize_cultures()
        # for i, text in enumerate(["Culture", "Mushroom", "Medium", "Passed"]):
        #     header = ttk.Label(self.frame, text=text)
        #     header.grid(row=0, column=i)
#
        # for i, _ in enumerate(self.entries, 1):
        #     cul_name = ttk.Label(self.frame, text=str(self.entries[i-1]["record"]))
        #     cul_name.grid(row=i, column=0, padx=5)
        #     cul_mushroom = ttk.Label(self.frame, text=self.entries[i-1]["record"].mushroom)
        #     cul_mushroom.grid(row=i, column=1, padx=5)
        #     cul_medium = ttk.Label(self.frame, text=self.entries[i-1]["record"].medium)
        #     cul_medium.grid(row=i, column=2, padx=5)
        #     check_box = ttk.Checkbutton(self.frame, variable=self.entries[i-1]["status_var"])
        #     check_box.grid(row=i, column=3)


class LabTab(tk.Frame):
    def __init__(self, parent, database):
        super().__init__(parent)

        create_panel = CreatePanel(self, database)
        notebook = ttk.Notebook(self)

        inspect_bag_panel = InspectBagPanel(notebook, "Inspect Bags", database, width=700)
        inspect_grain_spawn_panel = InspectGrainSpawnPanel(notebook, "Inspect Grain Spawn", database, width=700)
        inspect_culture_panel = InspectCulturePanel(notebook, "Inspect Cultures", database, width=700)

        for tab, lab in zip([inspect_bag_panel, inspect_grain_spawn_panel, inspect_culture_panel],
                            ["Bags", "Grain Spawn", "Cultures"]):
            notebook.add(tab, text=lab)

        create_panel.grid(row=0, column=1, sticky="ews")
        notebook.grid(row=0, column=1, sticky="news")

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=6)


class FinanceTab(tk.Frame):
    def __init__(self, parent, database):
        super().__init__(parent)
        self.database = database


class HistoryTab(tk.Frame):
    def __init__(self, parent, database):
        super().__init__(parent)
        self.database = database


class App(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self._set_style()
        self.title("PyLabBook")

        database = Database()
        database.connect()
        database.initialize_tables()

        notebook = ttk.Notebook(self)
        lab_tab = LabTab(notebook, database)
        lab_tab.pack(fill="both", expand=True)
        history_tab = HistoryTab(notebook, database)
        history_tab.pack(fill="both", expand=True)
        finance_tab = FinanceTab(notebook, database)
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
