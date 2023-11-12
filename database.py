import os
import sqlite3
import itertools
from datastructures import Recipe, Culture, GrainSpawn, Bag


class Database:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def connect(self):
        database_path = os.path.join("data", "pyLabBook.db")
        self.connection = sqlite3.connect(database_path)
        self.cursor = self.connection.cursor()

    def __initialize_recipe_table(self):

        sql = """
        CREATE TABLE IF NOT EXISTS recipes (
            recipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at DATETIME DEFAULT (current_date),
            name TEXT NOT NULL UNIQUE,
            recipe_type CHECK ( recipe_type in ('Growth Medium', 'Grain Spawn', 'Substrate') ),
            ingredients NOT NULL ,
            instructions NOT NULL)"""

        self.cursor.execute(sql)
        self.connection.commit()

    def __initialize_culture_table(self):
        sql = """
        CREATE TABLE IF NOT EXISTS cultures (
            culture_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at DATETIME DEFAULT (current_date),
            name TEXT NOT NULL UNIQUE,
            variant TEXT NOT NULL,
            mushroom TEXT NOT NULL,
            medium TEXT)"""
        self.cursor.execute(sql)
        self.connection.commit()

    def __initialize_grain_spawn_table(self):
        sql = """
        CREATE TABLE IF NOT EXISTS grain_spawn (
            grain_spawn_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at DATETIME DEFAULT (current_date),
            culture_id INTEGER,
            recipe_id INTEGER,
            FOREIGN KEY(culture_id) REFERENCES cultures(culture_id),
            FOREIGN KEY(recipe_id) REFERENCES recipes(recipe_id))"""
        self.cursor.execute(sql)
        self.connection.commit()

    def __initialize_bag_table(self):
        sql = """
        CREATE TABLE IF NOT EXISTS bags(
            bag_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at DATETIME DEFAULT (current_date),
            grain_spawn_id INTEGER,
            recipe_id INTEGER,
            FOREIGN KEY (grain_spawn_id) REFERENCES grain_spawn(grain_spawn_id),
            FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id))"""
        self.cursor.execute(sql)
        self.connection.commit()

    def __initialize_action_tables(self):
        sql = """
        CREATE TABLE IF NOT EXISTS culture_observations(
            culture_id INTEGER,
            observed_at DATETIME DEFAULT (current_date),
            action TEXT CHECK ( action in ('Created', 'Harvested', 'Destroyed') ),
            passed INTEGER NOT NULL CHECK ( passed in (0, 1) ),
            FOREIGN KEY (culture_id) REFERENCES cultures(culture_id));
    
        CREATE TABLE IF NOT EXISTS grain_spawn_observations(
            grain_spawn_id INTEGER,
            observed_at DATETIME DEFAULT (current_date),
            action TEXT CHECK ( action in ('Created', 'Used', 'Destroyed') ),
            passed INTEGER NOT NULL CHECK ( passed in (0, 1) ),
            FOREIGN KEY (grain_spawn_id) REFERENCES grain_spawn(grain_spawn_id));
        
        CREATE TABLE IF NOT EXISTS bag_observations(
            bag_id INTEGER,
            observed_at DATETIME DEFAULT (current_date),
            action TEXT CHECK ( action in ('Created', 'Harvested', 'Destroyed') ),
            passed INTEGER NOT NULL CHECK ( passed in (0, 1) ),
            FOREIGN KEY (bag_id) REFERENCES bags(bag_id));"""

        for statement in sql.split(";"):
            self.cursor.execute(statement)
        self.connection.commit()

    def __initialize_harvest_table(self):
        sql = """
        CREATE TABLE IF NOT EXISTS harvests(
            bag_id INTEGER,
            harvested_at DATETIME DEFAULT (current_date),
            yield_g FLOAT NOT NULL,
            FOREIGN KEY (bag_id) REFERENCES bags(bag_id))
        """
        self.cursor.execute(sql)
        self.connection.commit()

    def initialize_tables(self):
        self.__initialize_recipe_table()
        self.__initialize_culture_table()
        self.__initialize_grain_spawn_table()
        self.__initialize_bag_table()

        self.__initialize_action_tables()
        self.__initialize_harvest_table()

        # todo: extend me with financial and bi-tables

    def get_unique(self, column, table):
        sql = f"""SELECT DISTINCT {column} FROM {table} ORDER BY {column}"""
        result = self.connection.execute(sql)
        return list(itertools.chain.from_iterable(result))

    def get_unique_mushrooms(self):
        return self.get_unique("mushroom", "cultures")

    def get_unique_recipe_names(self, recipe_type):
        sql = """SELECT DISTINCT name FROM recipes WHERE recipe_type = $recipe_type"""
        result = self.connection.execute(sql, {"recipe_type": recipe_type})
        return list(itertools.chain.from_iterable(result))

    def get_recipes(self, recipe_type=None):
        sql = """SELECT recipe_id, name, recipe_type, ingredients, instructions FROM recipes"""
        result = [Recipe(*r) for r in self.connection.execute(sql)]

        if recipe_type is not None:
            out = {r.name: r for r in result if r.recipe_type == recipe_type}
        else:
            out = {r.name: r for r in result}
        return out

    def get_n(self, table, created_at):
        sql = f"SELECT count(*) FROM {table} WHERE date(created_at) = $created_at"
        result = self.cursor.execute(sql, {"created_at": created_at})
        out, = result.fetchone()
        return out

    def get_current(self):
        # todo: implement me!
        raise NotImplementedError

    def write(self, obj):
        if isinstance(obj, Recipe):
            self.__write_recipe(obj)
        if isinstance(obj, Culture):
            self.__write_culture(obj)
        # todo: implement me!
        else:
            raise NotImplementedError

    def __write_recipe(self, recipe):
        params = {'name': recipe.name,
                  'ingredients': recipe.ingredients,
                  'instructions': recipe.instructions,
                  'recipe_type': recipe.recipe_type}

        sql = f"""
        INSERT INTO recipes(name, recipe_type, ingredients, instructions) 
        VALUES ($name, $recipe_type, $ingredients, $instructions)"""
        self.cursor.execute(sql, params)
        self.connection.commit()

    def __write_culture(self, culture):
        params = {'name': str(culture),
                  'created_at': culture.created_at,
                  'variant': culture.variant,
                  'mushroom': culture.mushroom,
                  'medium': culture.medium}
        sql = """
        INSERT INTO cultures(name, created_at, variant, mushroom, medium)
        VALUES ($name, $created_at, $variant, $mushroom, $medium)"""
        self.cursor.execute(sql, params)
        self.connection.commit()


if __name__ == "__main__":
    database = Database()
    database.connect()
    database.initialize_tables()