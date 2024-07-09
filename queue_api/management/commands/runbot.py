from django.core.management.base import BaseCommand
import asyncio
from queue_api import bot


class Command(BaseCommand):
    def handle(self, *args, **options):
        asyncio.run(bot.main())