from src import db
from src.frontend import bot
import sys
import asyncio

if __name__ == '__main__':
    if len(sys.argv) > 1:
        match sys.argv[1]:
            case 'drop':
                db.drop_tables()
            case 'test':
                pass

    db.create_tables()
    asyncio.run(bot.main())