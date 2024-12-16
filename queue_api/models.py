from django.db import models


class Message(models.Model):
    event = models.ForeignKey('Event', on_delete=models.CASCADE)
    message_id = models.BigIntegerField(null=True)
    chat_id = models.BigIntegerField()


class Event(models.Model):
    text = models.CharField(max_length=512)
    date = models.DateTimeField()
    creator = models.ForeignKey('TelegramUser', on_delete=models.CASCADE)
    group = models.ForeignKey('TelegramGroup', on_delete=models.CASCADE)

    def __str__(self):
        return self.text


class TelegramUser(models.Model):
    tg_id = models.BigIntegerField(primary_key=True)
    full_name = models.CharField(max_length=128, null=True)
    groups = models.ManyToManyField('TelegramGroup', through='GroupMember')
    user_queue = models.ManyToManyField('Queue', through='QueueMember')
    tz = models.IntegerField(default=3)
    is_started = models.BooleanField(default=False)

    def __str__(self):
        return str(self.tg_id)


class TelegramGroup(models.Model):
    tg_id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=128)
    thread_id = models.BigIntegerField(null=True)
    main_admin = models.ForeignKey('TelegramUser', on_delete=models.RESTRICT, null=True)

    def __str__(self):
        return self.name


class GroupMember(models.Model):
    user = models.ForeignKey('TelegramUser', on_delete=models.CASCADE)
    groups = models.ForeignKey('TelegramGroup', on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)


class Student(models.Model):
    group_member = models.OneToOneField('GroupMember', on_delete=models.CASCADE, primary_key=True)
    date = models.DateTimeField(auto_now=True)
    prev_rating = models.SmallIntegerField(default=0)
    rating = models.FloatField(default=0)
    scholarship = models.FloatField(default=100)


class StudentGroup(models.Model):
    group = models.OneToOneField('TelegramGroup', primary_key=True, on_delete=models.CASCADE)
    thread_id = models.BigIntegerField(null=True)
    is_session = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)


class Queue(Event):
    is_rendering = models.BooleanField(default=False)


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


class Deadline(Event):
    pass


class Santa(Event):
    is_active = models.BooleanField(default=True)


class SantaMember(models.Model):
    user = models.ForeignKey('TelegramUser', on_delete=models.CASCADE)
    santa = models.ForeignKey('Santa', on_delete=models.CASCADE)


class DeadlineRequest(models.Model):
    user = models.ForeignKey('TelegramUser', on_delete=models.CASCADE)
    group = models.ForeignKey('TelegramGroup', on_delete=models.CASCADE)


class DeadlineStatus(models.Model):
    user = models.ForeignKey('TelegramUser', on_delete=models.CASCADE)
    deadline = models.ForeignKey('Deadline', on_delete=models.CASCADE)
    is_done = models.BooleanField(default=False)
