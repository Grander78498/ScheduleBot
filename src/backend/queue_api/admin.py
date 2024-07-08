from django.contrib import admin
from .models import *


admin.site.register(TelegramUser)
admin.site.register(TelegramGroup)
admin.site.register(Queue)