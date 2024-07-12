from django.core.management.base import BaseCommand
import asyncio
import bot


class Command(BaseCommand):
    def handle(self, *args, **options):
        asyncio.run(bot.main())