import os
import sqlite3
from datastructures import Recipe, Culture, GrainSpawn, Bag

def connect():
    database_path = os.path.join("data", "pyLabBook.db")
    con = sqlite3.connect(database_path)
    return con


def _initialize_recipe_table(con):
    cur = con.cursor()
    sql = """
    CREATE TABLE IF NOT EXISTS recipes (
        recipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at DATETIME DEFAULT (current_date),
        name NOT NULL UNIQUE,
        ingredients NOT NULL ,
        instructions NOT NULL)"""
    cur.execute(sql)
    con.commit()


def _initialize_bag_table(con):
    cur = con.cursor()
    sql = "CREATE TABLE bags()"


def initialize_tables(con):
    _initialize_recipe_table(con)
    # todo: implement me!
    # todo: extend me
    raise NotImplementedError


def initialize_tables():
    # todo: implement me!
    raise NotImplementedError


def get_current():
    # todo: implement me!
    raise NotImplementedError


def write(obj, con):
    if isinstance(obj, Recipe):
        _write_recipe(obj, con)
    # todo: implement me!
    else:
        raise NotImplementedError


def _write_recipe(recipe, con):
    name = recipe.name
    ingredients = recipe.ingredients
    instructions = recipe.instructions
    cursor = con.cursor()
    sql = f"INSERT INTO recipes(name, ingredients, instructions) VALUES ('{name}', '{ingredients}', '{instructions}')"
    print(sql)
    cursor.execute(sql)
    con.commit()
