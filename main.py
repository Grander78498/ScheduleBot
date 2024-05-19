from src.db import database, drop_tables, create_tables

create_tables.create_tables()
database.insert_user('Лёня')
database.insert_user('Влад')
database.insert_user('Саша')
database.test_db()