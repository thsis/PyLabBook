import os
import sqlite3
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from datetime import date, datetime

import tkcalendar
from tkcalendar import DateEntry

from datastructures import Recipe, Bag, Culture, GrainSpawn, CultureObservation, GrainSpawnObservation, BagObservation
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
    counter = ttk.Spinbox(parent, width=width, textvariable=variable, from_=1, to=1000, increment=1)
    counter.grid(row=row, column=column, **kwargs)
    return counter


class CreatePanel(tk.Frame):
    def __init__(self, parent, database, observed_at, padx=None, pady=None):
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
        self.observed_at = observed_at

        self.date_label = ttk.LabelFrame(self.frame, text="Date")
        self.date_label.grid(row=0, column=0, sticky="news", padx=padx, pady=pady)

        self.created_at_widget = DateEntry(self.date_label, date_pattern='y-mm-dd', textvariable=self.observed_at)
        self.created_at_widget.grid(row=0, column=0, sticky="news", padx=padx, pady=pady)

        self.label_frame = ttk.LabelFrame(self.frame, text="Create New")
        self.populate()
        self.label_frame.grid(row=1, column=0, sticky="nesw", padx=padx, pady=pady)
        self.frame.grid(row=0, column=0, sticky="nesw")

    def populate(self):
        for i, (text, command) in enumerate(self.buttons.items()):
            _place_button(self.label_frame, text, command, i, 0, padx=5, pady=5)

    def create_bag(self):
        def write_bag():
            nonlocal popup, grain_spawn
            try:
                count = count_var.get()
                starter = grain_spawn[grain_spawn_name_var.get()]
                recipe = recipes[recipe_name_var.get()]
                start = self.database.get_n("bags", created_at_var.get()) + 1
                for i in range(start, start + count):
                    bag = Bag(id=i,
                              created_at=created_at_var.get(),
                              grain_spawn_id=starter.id,
                              recipe_id=recipe.id)
                    self.database.write(bag)

                bag_str = 'Bag was' if count == 1 else 'Bags were'
                row_str = 's' if count != 1 else ''
                msg = f"{bag_str} added to database ({count} row{row_str})."
                messagebox.showinfo("", msg, parent=popup)
                popup.destroy()

            except (sqlite3.DatabaseError, sqlite3.IntegrityError) as e:
                messagebox.showerror("Error", e, parent=popup)
                raise e

        def update_recipe_panel(var, index, mode):
            selected = recipe_name_var.get()
            if recipe := recipes.get(selected):
                ingredients_panel.config(state=tk.NORMAL)
                instructions_panel.config(state=tk.NORMAL)
                ingredients_panel.delete(1.0, tk.END)
                instructions_panel.delete(1.0, tk.END)
                ingredients_panel.insert(1.0, recipe.ingredients)
                instructions_panel.insert(1.0, recipe.instructions)
                ingredients_panel.config(state=tk.DISABLED)
                instructions_panel.config(state=tk.DISABLED)

        def update_bag_title(var, index, mode):
            nonlocal grain_spawn, grain_spawn_selection_widget
            created_at = created_at_var.get()
            if created_at:
                text = self.get_next_bag_title(created_at)
                title_label.config(text=text)
                grain_spawn = self.get_current_experiments("grain_spawn", created_at_var.get())
                grain_spawn_selection_widget["values"] = list(grain_spawn.keys())

        def update_description_labels(var, index, mode):
            if culture_name := grain_spawn_name_var.get():
                culture = grain_spawn[culture_name]
                mushroom_label.config(text=culture.mushroom)
                variant_label.config(text=culture.variant)

        popup = _create_popup(self.parent)
        popup.title("Add New Bag")

        popup.grid_columnconfigure(0, weight=1)
        popup.grid_columnconfigure(1, weight=3)

        grain_spawn_name_var = tk.StringVar()
        grain_spawn_name_var.trace_add("write", update_description_labels)
        recipe_name_var = tk.StringVar()
        recipe_name_var.trace_add("write", update_recipe_panel)
        created_at_var = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        created_at_var.trace_add("write", update_bag_title)
        count_var = tk.IntVar(value=1)

        control_panel = ttk.Frame(popup)
        control_panel.grid(row=0, column=0, sticky="nw")
        recipe_panel = ttk.Frame(popup)
        recipe_panel.grid(row=0, column=1, sticky="news")

        recipes = self.database.get_recipes("Substrate")
        grain_spawn = self.get_current_experiments("grain_spawn", created_at_var.get())

        title_label = _place_label(control_panel, "", row=0, column=0, columnspan=2)
        _place_label(control_panel, "Grain Spawn:", row=1, column=0, sticky="news")
        grain_spawn_selection_widget = _place_selection(control_panel, list(grain_spawn.keys()), grain_spawn_name_var,
                                                        row=1, column=1, sticky="news")

        mushroom_label = _place_label(control_panel, "Mushroom", row=2, column=0, sticky="news")
        variant_label = _place_label(control_panel, "Variant", row=2, column=1, sticky="news")

        _place_label(control_panel, "Recipe:", row=3, column=0, sticky="news")
        _place_selection(control_panel, list(recipes.keys()), recipe_name_var, row=3, column=1, sticky="news")

        _place_label(control_panel, "Created At:", row=4, column=0, sticky="news")
        created_at_widget = DateEntry(control_panel, date_pattern='y-mm-dd', textvariable=created_at_var)
        created_at_widget.grid(row=4, column=1, sticky="news")

        _place_label(control_panel, "Amount:", row=5, column=0, sticky="news")
        _place_counter(control_panel, count_var, row=5, column=1)
        _place_button(control_panel, "Okay", write_bag, row=6, column=0, columnspan=2)

        _place_label(recipe_panel, "Ingredients", row=0, column=0)
        ingredients_panel = _place_text(recipe_panel, row=1, column=0, width=70, height=10, disable=True)
        _place_label(recipe_panel, "Instructions", row=2, column=0)
        instructions_panel = _place_text(recipe_panel, row=3, column=0, width=70, disable=True)

    def create_grain_spawn(self):
        def write_grain_spawn():
            nonlocal popup
            try:
                count = count_var.get()
                culture = cultures[culture_name_var.get()]
                recipe = recipes[recipe_name_var.get()]
                start = self.database.get_n("grain_spawn", created_at_var.get()) + 1
                for i in range(start, start + count):
                    grain_spawn = GrainSpawn(id=i,
                                             created_at=created_at_var.get(),
                                             culture_id=culture.id,
                                             recipe_id=recipe.id)
                    self.database.write(grain_spawn)
                msg = f"Grain Spawn was added to database ({count} row{'s' if count != 1 else ''})."
                messagebox.showinfo("", msg, parent=popup)
                popup.destroy()

            except (sqlite3.DatabaseError, sqlite3.IntegrityError) as e:
                messagebox.showerror("Error", e, parent=popup)
                raise e

        def update_recipe_panel(var, index, mode):
            selected = recipe_name_var.get()
            if recipe := recipes.get(selected):
                ingredients_panel.config(state=tk.NORMAL)
                instructions_panel.config(state=tk.NORMAL)
                ingredients_panel.delete(1.0, tk.END)
                instructions_panel.delete(1.0, tk.END)
                ingredients_panel.insert(1.0, recipe.ingredients)
                instructions_panel.insert(1.0, recipe.instructions)
                ingredients_panel.config(state=tk.DISABLED)
                instructions_panel.config(state=tk.DISABLED)

        def update_grain_spawn_title(var, index, mode):
            nonlocal cultures, culture_selection_widget
            created_at = created_at_var.get()
            if created_at:
                text = self.get_next_grain_spawn_title(created_at)
                title_label.config(text=text)
                cultures = self.get_current_experiments("cultures", created_at_var.get())
                culture_selection_widget["values"] = list(cultures.keys())

        def update_description_labels(var, index, mode):
            if culture_name := culture_name_var.get():
                culture = cultures[culture_name]
                mushroom_label.config(text=culture.mushroom)
                variant_label.config(text=culture.variant)

        popup = _create_popup(self.parent)
        popup.title("Add New Grain Spawn")
        popup.grid_columnconfigure(0, weight=1)
        popup.grid_columnconfigure(1, weight=3)

        culture_name_var = tk.StringVar()
        culture_name_var.trace_add("write", update_description_labels)
        recipe_name_var = tk.StringVar()
        recipe_name_var.trace_add("write", update_recipe_panel)
        created_at_var = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        created_at_var.trace_add("write", update_grain_spawn_title)
        count_var = tk.IntVar(value=1)

        recipes = self.database.get_recipes("Grain Spawn")
        cultures = self.get_current_experiments("cultures", created_at_var.get())

        control_panel = ttk.Frame(popup)
        control_panel.grid(row=0, column=0, sticky="nw")
        recipe_panel = ttk.Frame(popup)
        recipe_panel.grid(row=0, column=1, sticky="news")

        title_label = _place_label(control_panel, "", row=0, column=0, columnspan=2)
        _place_label(control_panel, "Culture:", row=1, column=0, sticky="news")
        culture_selection_widget = _place_selection(control_panel, list(cultures.keys()), culture_name_var,
                                                    row=1, column=1, sticky="news")

        mushroom_label = _place_label(control_panel, "Mushroom", row=2, column=0, sticky="news")
        variant_label = _place_label(control_panel, "Variant", row=2, column=1, sticky="news")

        _place_label(control_panel, "Recipe:", row=3, column=0, sticky="news")
        _place_selection(control_panel, list(recipes.keys()), recipe_name_var, row=3, column=1, sticky="news")

        _place_label(control_panel, "Created At:", row=4, column=0, sticky="news")
        created_at_widget = DateEntry(control_panel, date_pattern='y-mm-dd', textvariable=created_at_var)
        created_at_widget.grid(row=4, column=1, sticky="news")

        _place_label(control_panel, "Amount:", row=5, column=0, sticky="news")
        _place_counter(control_panel, count_var, row=5, column=1)
        _place_button(control_panel, "Okay", write_grain_spawn, row=6, column=0, columnspan=2)

        _place_label(recipe_panel, "Ingredients", row=0, column=0)
        ingredients_panel = _place_text(recipe_panel, row=1, column=0, width=70, height=10, disable=True)
        _place_label(recipe_panel, "Instructions", row=2, column=0)
        instructions_panel = _place_text(recipe_panel, row=3, column=0, width=70, disable=True)

    def get_current_experiments(self, experiment_type, observed_at):
        if experiment_type == "cultures":
            return {str(c): c for c in self.database.get_current_cultures(observed_at)}
        elif experiment_type == "grain_spawn":
            return {str(g): g for g in self.database.get_current_grain_spawn(observed_at)}
        elif experiment_type == "bags":
            return {str(b): b for b in self.database.get_current_bags(observed_at)}

    def get_next_culture_title(self, created_at):
        counter = self.database.get_n(table="cultures", created_at=created_at) + 1
        culture = Culture(created_at=created_at,
                          id=counter,
                          mushroom="",
                          variant="",
                          medium="")
        return str(culture)

    def get_next_grain_spawn_title(self, created_at):
        counter = self.database.get_n(table="grain_spawn", created_at=created_at) + 1
        grain_spawn = GrainSpawn(created_at=created_at,
                                 id=counter,
                                 recipe_id=-1,
                                 culture_id=-1)
        return str(grain_spawn)

    def get_next_bag_title(self, created_at):
        counter = self.database.get_n(table="bags", created_at=created_at) + 1
        bag = Bag(created_at=created_at,
                  id=counter,
                  recipe_id=-1,
                  grain_spawn_id=-1)
        return str(bag)

    def create_culture(self):
        def write_culture():
            nonlocal popup
            try:
                culture = Culture(id=self.database.get_n("cultures", created_at_var.get()) + 1,
                                  variant=variant_name.get(),
                                  created_at=created_at_var.get(),
                                  medium=medium_var.get(),
                                  mushroom=mushroom_var.get())

                self.database.write(culture)
                messagebox.showinfo("", "Culture was added to database.", parent=popup)
                popup.destroy()
            except (sqlite3.DatabaseError, sqlite3.IntegrityError) as e:
                messagebox.showerror("Error", e, parent=popup)
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

        title_label = _place_label(control_panel, "", row=0, column=0, columnspan=2)
        _place_label(control_panel, "Variant:", row=1, column=0, sticky="news")
        _place_entry(control_panel, variant_name, row=1, column=1, sticky="news")

        _place_label(control_panel, "Mushroom:", row=2, column=0, sticky="news")
        _place_selection(control_panel, mushrooms, mushroom_var, row=2, column=1, sticky="news")
        _place_label(control_panel, "Medium:", row=3, column=0, sticky="news")
        _place_selection(control_panel, list(recipes.keys()), medium_var, row=3, column=1, sticky="news")

        _place_label(control_panel, "Created At:", row=4, column=0, sticky="news")
        created_at_widget = DateEntry(control_panel, date_pattern='y-mm-dd', textvariable=created_at_var)
        created_at_widget.grid(row=4, column=1, sticky="news")

        _place_button(control_panel, "Okay", write_culture, row=5, column=0, columnspan=2)

        _place_label(recipe_panel, "Ingredients", row=0, column=0)
        ingredients_panel = _place_text(recipe_panel, row=1, column=0, width=70, height=10, disable=True)
        _place_label(recipe_panel, "Instructions", row=2, column=0)
        instructions_panel = _place_text(recipe_panel, row=3, column=0, width=70, disable=True)

    def create_recipe(self):
        def write_recipe():
            nonlocal popup
            name = name_var.get()
            recipe_type = type_var.get()
            ingredients = ingredients_text.get("0.0", tk.END)
            instructions = instructions_text.get("0.0", tk.END)

            try:
                recipe = Recipe(id=None,
                                name=name,
                                recipe_type=recipe_type,
                                ingredients=ingredients,
                                instructions=instructions)
                self.database.write(recipe)
                messagebox.showinfo("", "Recipe written to database!", parent=popup)
                popup.destroy()
            except AssertionError:
                messagebox.showerror("Error", "Recipe Name, Ingredients or Instructions cannot be empty", parent=popup)
            except (sqlite3.DatabaseError, sqlite3.IntegrityError) as e:
                messagebox.showerror("Error", e, parent=popup)
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
    def __init__(self, parent, title, database, observed_at, width=None):
        super().__init__(parent)
        # todo: look at this again... try to make widget-canvas resize with window
        self.database = database
        self.entries = []
        self.check_results = []
        self.actions = []
        self.observed_at = observed_at

        self.label_frame = ttk.LabelFrame(self, text=title, width=width)
        self.label_frame.grid(row=0, column=0, pady=(20, 5), padx=20, sticky="news")
        self.label_frame.grid_columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(self.label_frame, borderwidth=0, width=width)

        self.frame = tk.Frame(self.canvas, width=width)
        self.vsb = tk.Scrollbar(self.label_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(fill="both", expand=True)
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

    def clear(self):
        self.entries = []
        self.check_results = []
        self.actions = []
        for widget in self.frame.winfo_children():
            widget.destroy()

    def populate(self):
        raise NotImplementedError

    def confirm(self):
        try:
            observed_at = self.observed_at.get()
            for entry, check, action in zip(self.entries, self.check_results, self.actions):
                entry.passed = check.get()
                entry.action = action.get()
                entry.observed_at = observed_at

            self.database.write(self.entries)
            messagebox.showinfo("", "Observations written to database.", parent=self)
        except Exception as e:
            messagebox.showerror("Error!", str(e))
            raise e

    def reset(self):
        for action, check in zip(self.actions, self.check_results):
            action.set("")
            check.set(False)

    def mark_all_ok(self):
        for check in self.check_results:
            check.set(True)

    def on_frame_configure(self, event):
        """Reset the scroll region to encompass the inner frame"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


class InspectBagPanel(InspectPanel):
    def __init__(self, parent, title, database, observed_at, width=None):
        super().__init__(parent, title, database, observed_at, width)
        self.harvested = []

    def clear(self):
        super().clear()
        self.harvested = []

    def populate(self):

        self.clear()
        observed_at = self.observed_at.get()
        action_values = ['', 'Created', 'Destroyed', 'Kneaded', 'Harvested']
        self.entries = [BagObservation(g, observed_at, False, "") for g in self.database.get_current_bags(observed_at)]
        self.check_results = [tk.IntVar(self, value=0) for _ in self.entries]
        self.actions = [tk.StringVar(value="") for _ in self.entries]
        self.harvested = [tk.DoubleVar() for _ in self.entries]

        for i, text in enumerate(["Bag", "Mushroom", "Variant", "Created At", "Passed", "Action", "Yield"]):
            _place_label(self.frame, text=text, row=0, column=i)

        for i, _ in enumerate(self.entries):
            _place_label(self.frame, text=str(self.entries[i].experiment), row=i + 1, column=0, padx=5)
            _place_label(self.frame, text=self.entries[i].experiment.mushroom, row=i + 1, column=1, padx=5)
            _place_label(self.frame, text=self.entries[i].experiment.variant, row=i + 1, column=2, padx=5)
            _place_label(self.frame,
                         text=self.entries[i].experiment.created_at.strftime("%Y-%m-%d"),
                         row=i + 1, column=3, padx=5)
            _place_checkbox(self.frame, self.check_results[i], row=i + 1, column=4, padx=5)
            _place_selection(self.frame, values=action_values, variable=self.actions[i], row=i + 1, column=5, padx=5)
            _place_entry(self.frame, variable=self.harvested[i], row=i + 1, column=6, padx=5)

    def confirm(self):
        try:
            observed_at = self.observed_at.get()
            for entry, check, action, harvested in zip(self.entries, self.check_results, self.actions, self.harvested):
                entry.passed = check.get()
                entry.action = action.get()
                entry.observed_at = observed_at
                entry.harvested = harvested.get()

            self.database.write(self.entries)
            messagebox.showinfo("", "Observations written to database.",
                                parent=self)
        except Exception as e:
            messagebox.showerror("Error!", str(e))
            raise e


class InspectGrainSpawnPanel(InspectPanel):
    def __init__(self, parent, title, database, observed_at, width=None):
        super().__init__(parent, title, database, observed_at, width)

    def populate(self):
        self.clear()
        obs = self.observed_at.get()
        action_values = ['', 'Created', 'Inoculated', 'Shaken', 'Destroyed', 'Used']
        self.entries = [GrainSpawnObservation(g, obs, False, "") for g in self.database.get_current_grain_spawn(obs)]
        self.check_results = [tk.IntVar(self, value=0) for _ in self.entries]
        self.actions = [tk.StringVar(value="") for _ in self.entries]

        for i, text in enumerate(["Grain Spawn", "Mushroom", "Variant", "Created At", "Passed", "Action"]):
            _place_label(self.frame, text=text, row=0, column=i)

        for i, _ in enumerate(self.entries):
            _place_label(self.frame, text=str(self.entries[i].experiment), row=i + 1, column=0, padx=5)
            _place_label(self.frame, text=self.entries[i].experiment.mushroom, row=i + 1, column=1, padx=5)
            _place_label(self.frame, text=self.entries[i].experiment.variant, row=i + 1, column=2, padx=5)
            _place_label(self.frame, text=self.entries[i].experiment.created_at.strftime("%Y-%m-%d"),
                         row=i + 1, column=3, padx=5)
            _place_checkbox(self.frame, self.check_results[i], row=i + 1, column=4, padx=5)
            _place_selection(self.frame, values=action_values, variable=self.actions[i], row=i + 1, column=5, padx=5)


class InspectCulturePanel(InspectPanel):
    def __init__(self, parent, title, database, observed_at, width=None):
        super().__init__(parent, title, database, observed_at, width)

    def populate(self):
        self.clear()
        obs = self.observed_at.get()
        action_values = ['', 'Created', 'Destroyed']
        self.entries = [CultureObservation(c, obs, True, "") for c in self.database.get_current_cultures(obs)]
        self.check_results = [tk.IntVar(self, value=1) for _ in self.entries]
        self.actions = [tk.StringVar(value="") for _ in self.entries]

        for i, text in enumerate(["Culture", "Mushroom", "Variant", "Medium", "Passed"]):
            _place_label(self.frame, text=text, row=0, column=i)
#
        for i, _ in enumerate(self.entries):
            _place_label(self.frame, text=str(self.entries[i].experiment.name), row=i+1, column=0, padx=5)
            _place_label(self.frame, text=self.entries[i].experiment.mushroom, row=i+1, column=1, padx=5)
            _place_label(self.frame, text=self.entries[i].experiment.variant, row=i+1, column=2, padx=5)
            _place_label(self.frame, text=self.entries[i].experiment.medium, row=i+1, column=3, padx=5)
            _place_checkbox(self.frame, self.check_results[i], row=i+1, column=4, padx=5)
            _place_selection(self.frame, values=action_values, variable=self.actions[i], row=i+1, column=5, padx=5)


class LabTab(tk.Frame):
    def __init__(self, parent, database):
        super().__init__(parent)

        observed_at = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))

        create_panel = CreatePanel(self, database, observed_at)
        self.notebook = ttk.Notebook(self)

        self.inspect_bag_panel = InspectBagPanel(self.notebook,
                                                 "Inspect Bags", database, observed_at, width=700)
        self.inspect_grain_spawn_panel = InspectGrainSpawnPanel(self.notebook,
                                                                "Inspect Grain Spawn", database, observed_at, width=700)
        self.inspect_culture_panel = InspectCulturePanel(self.notebook,
                                                         "Inspect Cultures", database, observed_at, width=700)

        for tab, lab in zip([self.inspect_bag_panel, self.inspect_grain_spawn_panel, self.inspect_culture_panel],
                            ["Bags", "Grain Spawn", "Cultures"]):
            self.notebook.add(tab, text=lab)

        create_panel.grid(row=0, column=1, sticky="ews")
        self.notebook.grid(row=0, column=1, sticky="news")

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=6)
        for i in range(1, 3):
            self.grid_rowconfigure(i, weight=1)
        observed_at.trace_add("write", self.update_contents)

    def update_contents(self, var, index, mode):
        self.inspect_culture_panel.populate()
        self.inspect_grain_spawn_panel.populate()
        self.inspect_bag_panel.populate()


class FinanceTab(tk.Frame):
    def __init__(self, parent, database):
        super().__init__(parent)
        self.database = database


class HistoryTab(tk.Frame):
    def __init__(self, parent, database):
        super().__init__(parent)
        self.database = database
        self.calendar = tkcalendar.Calendar(self)
        self.calendar.grid(row=0, column=0, sticky="news")
        self.calendar.tag_config('Destroyed', background="red")

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.update_calendar()

    def update_calendar(self):
        for (date, msg, action) in self.database.get_actions():
            self.calendar.calevent_create(date=datetime.strptime(date, "%Y-%m-%d"), text=msg, tags=[action])


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
    app.mainloop()
