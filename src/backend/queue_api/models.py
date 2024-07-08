from django.db import models


class TelegramUser(models.Model):
    tg_id = models.BigIntegerField(primary_key=True)
    full_name = models.CharField(max_length=128, null=True)
    is_admin = models.BooleanField()
    group = models.ManyToManyField('TelegramGroup')
    queue = models.ManyToManyField('Queue', through='QueueMember')


class TelegramGroup(models.Model):
    tg_id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=128)
    thread_id = models.BigIntegerField(null=True)


class Queue(models.Model):
    message = models.CharField(max_length=64)
    date = models.DateTimeField()
    tz = models.IntegerField()
    creator = models.ForeignKey('TelegramUser', on_delete=models.CASCADE, related_name='creator')
    group = models.ForeignKey('TelegramGroup', on_delete=models.CASCADE)
    message_id = models.BigIntegerField(null=True)


class QueueMember(models.Model):
    user = models.ForeignKey('TelegramUser', on_delete=models.CASCADE)
    queue = models.ForeignKey('Queue', on_delete=models.CASCADE)
    vote_time = models.DateTimeField(auto_now_add=True)
