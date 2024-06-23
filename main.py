from src import database
# from src import bot
from src import new_database
import sys
import asyncio

if __name__ == '__main__':
    if len(sys.argv) > 1:
        match sys.argv[1]:
            case 'drop':
                database.drop_tables()
            case 'test':
                new_database.main()

    # database.create_tables()
    # asyncio.run(bot.main())