"""
TODO: добавить пояснения к каждому классу по поводу порядка параметров
"""

class ModelObject:
    def __init__(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def __str__(self):
        return str(self.__dict__)


class User(ModelObject):
    def __init__(self, *args, **kwargs):
        if not kwargs:
            attributes = ['user_id', 'full_name']
            super().__init__(**{key: value for key, value in zip(attributes, args)})
        else:
            super().__init__(**kwargs)


class Queue(ModelObject):
    def __init__(self, *args, **kwargs):
        if not kwargs:
            attributes = ['message', 'date', 'tz', 'is_started', 'is_notified',
                          'creator_id', 'group_tg_id', 'message_id', 'queue_message_id']
            super().__init__(**{key: value for key, value in zip(attributes, args)})
        else:
            super().__init__(**kwargs)


class QueueMember(ModelObject):
    def __init__(self, *args, **kwargs):
        if not kwargs:
            attributes = ['user_id', 'queue_id', 'vote_time']
            super().__init__(**{key: value for key, value in zip(attributes, args)})
        else:
            super().__init__(**kwargs)


class Admin(ModelObject):
    def __init__(self, *args, **kwargs):
        if not kwargs:
            attributes = ['user_id', 'group_id']
            super().__init__(**{key: value for key, value in zip(attributes, args)})
        else:
            super().__init__(**kwargs)


class Group(ModelObject):
    def __init__(self, *args, **kwargs):
        if not kwargs:
            attributes = ['group_id', 'group_name', 'thread_id']
            super().__init__(**{key: value for key, value in zip(attributes, args)})
        else:
            super().__init__(**kwargs)
