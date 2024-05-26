from src import database
from src import bot
import sys
import asyncio

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'drop':
        database.drop_tables()
    database.create_tables()
    asyncio.run(bot.main())