import os
import sqlite3
import itertools
from datastructures import Recipe, Culture, GrainSpawn, Bag, CultureObservation, GrainSpawnObservation, BagObservation


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
            name TEXT NOT NULL UNIQUE,
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
            name TEXT NOT NULL UNIQUE,
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
            action TEXT CHECK ( action in ('Created', 'Destroyed') OR action IS NULL ),
            passed INTEGER NOT NULL CHECK ( passed in (0, 1) ),
            FOREIGN KEY (culture_id) REFERENCES cultures(culture_id),
            PRIMARY KEY (culture_id, observed_at));
    
        CREATE TABLE IF NOT EXISTS grain_spawn_observations(
            grain_spawn_id INTEGER,
            observed_at DATETIME DEFAULT (current_date),
            action TEXT CHECK ( action in ('Created', 'Used', 'Destroyed') OR action IS NULL ),
            passed INTEGER NOT NULL CHECK ( passed in (0, 1) ),
            FOREIGN KEY (grain_spawn_id) REFERENCES grain_spawn(grain_spawn_id),
            PRIMARY KEY (grain_spawn_id, observed_at));
        
        CREATE TABLE IF NOT EXISTS bag_observations(
            bag_id INTEGER,
            observed_at DATETIME DEFAULT (current_date),
            action TEXT CHECK ( action in ('Created', 'Harvested', 'Destroyed') OR action IS NULL ),
            passed INTEGER NOT NULL CHECK ( passed in (0, 1) ),
            harvested FLOAT,
            FOREIGN KEY (bag_id) REFERENCES bags(bag_id),
            PRIMARY KEY (bag_id, observed_at));"""

        for statement in sql.split(";"):
            self.cursor.execute(statement)
        self.connection.commit()

    def initialize_tables(self):
        self.__initialize_recipe_table()
        self.__initialize_culture_table()
        self.__initialize_grain_spawn_table()
        self.__initialize_bag_table()
        self.__initialize_action_tables()


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

    def get_current_bags(self, date):
        sql = """
        WITH
        
        current_bags AS (
            SELECT
                bags.created_at,
                bags.bag_id,
                bags.grain_spawn_id,
                bags.recipe_id
            FROM bags
            WHERE NOT EXISTS(SELECT 1
                             FROM bag_observations obs
                             WHERE obs.bag_id = bags.bag_id
                               AND obs.action in ('Harvested', 'Destroyed')
                               AND obs.observed_at <= $date)
              AND bags.created_at <= $date),
                               
        bag_info AS (
            SELECT
                grain_spawn.grain_spawn_id,
                cultures.mushroom,
                cultures.variant
            FROM grain_spawn
            LEFT JOIN cultures USING (culture_id))
            
        SELECT 
            created_at,
            bag_id,
            grain_spawn_id,
            recipe_id,
            mushroom,
            variant
        FROM current_bags
        LEFT JOIN bag_info USING (grain_spawn_id)
        """
        out = [Bag(*b) for b in self.cursor.execute(sql, {"date": date})]
        return out

    def get_current_grain_spawn(self, date):
        sql = """
        WITH 
        
        current_grain_spawn AS (
            SELECT
                date(created_at) as created_at,
                grain_spawn_id,
                culture_id,
                recipe_id
            FROM grain_spawn gra
            WHERE NOT EXISTS(SELECT 1
                             FROM grain_spawn_observations obs
                             WHERE obs.grain_spawn_id = gra.grain_spawn_id
                               AND (obs.action in ('Destroyed', 'Used') AND obs.observed_at <= $date))
              AND gra.created_at <= $date),
        
        grain_spawn_info AS (
            SELECT
                culture_id,
                mushroom,
                variant
            FROM cultures)
            
        SELECT
            created_at,
            grain_spawn_id,
            culture_id,
            recipe_id,
            mushroom,
            variant
        FROM current_grain_spawn
        LEFT JOIN grain_spawn_info USING (culture_id)                     
        """
        out = [GrainSpawn(*g) for g in self.cursor.execute(sql, {"date": date})]
        return out

    def get_current_cultures(self, date):
        sql = """
        SELECT 
            cul.created_at, 
            cul.culture_id,
            cul.mushroom,
            cul.variant,
            cul.medium
        FROM cultures cul
        WHERE NOT EXISTS(SELECT 1
                         FROM culture_observations obs
                         WHERE obs.culture_id = cul.culture_id
                           AND obs.action = 'Destroyed'
                           AND (obs.observed_at <= $date AND cul.created_at >= $date))
        """
        out = [Culture(*c) for c in self.cursor.execute(sql, {"date": date})]
        return out

    def write(self, obj):
        if isinstance(obj, list):
            for o in obj:
                self.write(o)
        elif isinstance(obj, Recipe):
            self.__write_recipe(obj)
        elif isinstance(obj, Culture):
            self.__write_culture(obj)
        elif isinstance(obj, GrainSpawn):
            self.__write_grain_spawn(obj)
        elif isinstance(obj, Bag):
            self.__write_bag(obj)
        elif isinstance(obj, CultureObservation):
            self.__write_culture_observation(obj)
        elif isinstance(obj, GrainSpawnObservation):
            self.__write_grain_spawn_observation(obj)
        elif isinstance(obj, BagObservation):
            self.__write_bag_observation(obj)
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

    def __write_grain_spawn(self, grain_spawn):
        params = {'name': str(grain_spawn),
                  'created_at': grain_spawn.created_at,
                  'culture_id': grain_spawn.culture_id,
                  'recipe_id': grain_spawn.recipe_id}
        sql = """
        INSERT INTO grain_spawn(name, created_at, culture_id, recipe_id)
        VALUES ($name, $created_at, $culture_id, $recipe_id)"""
        self.cursor.execute(sql, params)
        self.connection.commit()

    def __write_bag(self, bag):
        params = {'name': bag.name,
                  'created_at': bag.created_at,
                  'grain_spawn_id': bag.grain_spawn_id,
                  'recipe_id': bag.recipe_id}
        sql = """
        INSERT INTO bags(name, created_at, grain_spawn_id, recipe_id)
        VALUES ($name, $created_at, $grain_spawn_id, $recipe_id)"""
        self.cursor.execute(sql, params)
        self.connection.commit()

    def __write_culture_observation(self, culture_observation: CultureObservation):
        params = {'culture_id': culture_observation.experiment.id,
                  'observed_at': culture_observation.observed_at,
                  'action': None if culture_observation.action == "" else culture_observation.action,
                  'passed': culture_observation.passed}

        sql = """
        INSERT INTO culture_observations(culture_id, observed_at, action, passed)
        VALUES ($culture_id, $observed_at, $action, $passed)
        ON CONFLICT (culture_id, observed_at) DO UPDATE SET action=excluded.action, passed=excluded.passed"""
        self.cursor.execute(sql, params)
        self.connection.commit()

    def __write_grain_spawn_observation(self, grain_spawn_observation: GrainSpawnObservation):
        params = {'grain_spawn_id': grain_spawn_observation.experiment.id,
                  'observed_at': grain_spawn_observation.observed_at,
                  'action': None if grain_spawn_observation.action == "" else grain_spawn_observation.action,
                  'passed': grain_spawn_observation.passed}

        sql = """
        INSERT INTO grain_spawn_observations(grain_spawn_id, observed_at, action, passed)
        VALUES ($grain_spawn_id, $observed_at, $action, $passed)
        ON CONFLICT (grain_spawn_id, observed_at) DO UPDATE SET action=excluded.action, passed=excluded.passed"""
        self.cursor.execute(sql, params)
        self.connection.commit()

    def __write_bag_observation(self, bag_observation: BagObservation):
        params = {'bag_id': bag_observation.experiment.id,
                  'observed_at': bag_observation.observed_at,
                  'action': None if bag_observation.action == "" else bag_observation.action,
                  'passed': bag_observation.passed,
                  'harvested': bag_observation.harvested}

        sql = """
        INSERT INTO bag_observations(bag_id, observed_at, action, passed, harvested)
        VALUES ($bag_id, $observed_at, $action, $passed, $harvested)
        ON CONFLICT (bag_id, observed_at) 
        DO UPDATE SET action=excluded.action, passed=excluded.passed, harvested=excluded.harvested
        """
        self.cursor.execute(sql, params)
        self.connection.commit()

    def get_culture_by_id(self, ids):
        sql = f"""
        SELECT 
            created_at, 
            culture_id, 
            mushroom, 
            variant,
            medium 
        FROM cultures
        WHERE culture_id in ({','.join(['?'] * len(ids))})"""

        return {c[1]: Culture(*c) for c in self.cursor.execute(sql, ids)}


if __name__ == "__main__":
    database = Database()
    database.connect()
    database.initialize_tables()