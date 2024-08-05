from django.core.management.base import BaseCommand
from argparse import ArgumentParser
import asyncio
from bot import main


class Command(BaseCommand):
    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument('-d', '--debug', const=None, nargs='?',
                            help="Запускает бота в режиме дебага (по умолчанию)")
        parser.add_argument('-p', '--prod', const=None, nargs='?',
                            help="Запускает бота в боевом режиме")

    def handle(self, *args, **options):
        asyncio.run(main())
