from django.db import models


class TelegramUser(models.Model):
    tg_id = models.BigIntegerField(primary_key=True)
    full_name = models.CharField(max_length=128, null=True)
    groups = models.ManyToManyField('TelegramGroup', through='GroupMember')
    queue = models.ManyToManyField('Queue', through='QueueMember')
    tz = models.IntegerField(default=3)
    is_started = models.BooleanField(default=False)


    def __str__(self):
        return str(self.tg_id)


class TelegramGroup(models.Model):
    tg_id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=128)
    thread_id = models.BigIntegerField(null=True)

    def __str__(self):
        return self.name


class GroupMember(models.Model):
    user = models.ForeignKey('TelegramUser', on_delete=models.CASCADE)
    groups = models.ForeignKey('TelegramGroup', on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)


class Queue(models.Model):
    message = models.CharField(max_length=64)
    date = models.DateTimeField()
    creator = models.ForeignKey('TelegramUser', on_delete=models.CASCADE, related_name='creator')
    group = models.ForeignKey('TelegramGroup', on_delete=models.CASCADE)
    message_id = models.BigIntegerField(null=True)
    renders = models.BigIntegerField(default=0)
    is_rendering = models.BooleanField(default=False)

    def __str__(self):
        return self.message


class QueueMember(models.Model):
    user = models.ForeignKey('TelegramUser', on_delete=models.CASCADE)
    queue = models.ForeignKey('Queue', on_delete=models.CASCADE)
    vote_time = models.DateTimeField(auto_now_add=True)
    # has_in_request = models.BooleanField(default=False)
    # has_out_request = models.BooleanField(default=False)
    # sent_request_time = models.DateTimeField(auto_now=True)


class SwapRequest(models.Model):
    first_member = models.ForeignKey('QueueMember', on_delete=models.CASCADE, related_name='first_member')
    second_member = models.ForeignKey('QueueMember', on_delete=models.CASCADE, related_name='second_member')
    first_message_id = models.BigIntegerField(null=True)
    second_message_id = models.BigIntegerField(null=True)
