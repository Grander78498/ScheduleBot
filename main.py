from src import database

database.drop_tables()
database.create_tables()
database.insert_notifications(81677486, 'Lol',
                              ['21.05.2024 19:28', '21.05.2024 19:29', '21.05.2024 19:26', '21.05.2024 19:27'], '3')
print(database.get_user_notifications(81677486))