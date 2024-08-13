from aiogram.fsm.state import StatesGroup, State


class Event(StatesGroup):
    group_id = State()
    text = State()
    hm = State()
    sec = State()
    swap = State()
    tz = State()
    event_type = State()
    set_main_admin = State()
    event_message_id = State()


class Deadline(StatesGroup):
    renameDeadline = State()
    deadline_roots = State()


class Calendar(StatesGroup):
    year = State()
    month = State()
    day = State()
    RemoveMessageyear = State()
    RemoveMessagemonth = State()
    RemoveMessageday = State()


class Queue(StatesGroup):
    renameQueue = State()
    deleteQueueMember = State()