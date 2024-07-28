from django.contrib import admin
from .models import *


admin.site.register(TelegramUser)
admin.site.register(TelegramGroup)
admin.site.register(Queue)
admin.site.register(GroupMember)
admin.site.register(QueueMember)
admin.site.register(SwapRequest)