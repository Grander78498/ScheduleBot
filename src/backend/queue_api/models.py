from django.db import models


class TelegramUser(models.Model):
    tg_id = models.BigIntegerField(primary_key=True)
    full_name = models.CharField(max_length=128, null=True)
    is_admin = models.BooleanField()
    groups = models.ManyToManyField('TelegramGroup')
    queue = models.ManyToManyField('Queue', through='QueueMember', null=True)

    def __str__(self):
        return str(self.tg_id)


class TelegramGroup(models.Model):
    tg_id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=128)
    thread_id = models.BigIntegerField(null=True)

    def __str__(self):
        return self.name


class Queue(models.Model):
    message = models.CharField(max_length=64)
    date = models.DateTimeField()
    tz = models.IntegerField()
    creator = models.ForeignKey('TelegramUser', on_delete=models.CASCADE, related_name='creator')
    group = models.ForeignKey('TelegramGroup', on_delete=models.CASCADE)
    message_id = models.BigIntegerField(null=True)

    def __str__(self):
        return self.message


class QueueMember(models.Model):
    user = models.ForeignKey('TelegramUser', on_delete=models.CASCADE)
    queue = models.ForeignKey('Queue', on_delete=models.CASCADE)
    vote_time = models.DateTimeField(auto_now_add=True)
