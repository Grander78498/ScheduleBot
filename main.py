from src import database

database.drop_tables()
database.create_tables()
database.add_admins(127124, [2142418, 12442133], 'Говно')
print(database.get_admins(127124))