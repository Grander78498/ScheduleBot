from aiogram.filters.callback_data import CallbackData


class ReturnToQueueList(CallbackData, prefix="return"):
    messageID: int


class YearCallback(CallbackData, prefix="year"):
    year: int


class MonthCallback(CallbackData, prefix="month"):
    month: int


class DayCallback(CallbackData, prefix="day"):
    day: int


class DeleteFirstQueueCallback(CallbackData, prefix="delete_first"):
    queueID: int


class GroupSelectCallback(CallbackData, prefix="selectGroup"):
    groupID: int
    is_admin: bool

class ChristmasGroupSelectCallback(CallbackData, prefix="chselectGroup"):
    groupID: int
    is_admin: bool



class QueueIDCallback(CallbackData, prefix="queueID"):
    queueID: int


class RemoveMyself(CallbackData, prefix="RemoveMyself"):
    queueID: int


class FindMyself(CallbackData, prefix="FindMyself"):
    queueID: int


class RemoveSwapRequest(CallbackData, prefix="Rsq"):
    first_user_id: int
    second_user_id: int
    first_m_id: int
    second_m_id: int
    queue_id: int


class AdminQueueSelectCallback(CallbackData, prefix="aqs"):
    queueID: int
    delete_message_id: int
    queueName: str

class SimpleQueueSelectCallback(CallbackData, prefix="sqs"):
    queueID: int
    delete_message_id: int
    queueName: str

class QueueSelectForSwapCallback(CallbackData, prefix="qss"):
    queueID: int
    queueName: str


class DeleteQueueCallback(CallbackData, prefix="DeleteQueue"):
    queueID: int
    messageID: int


class DeleteQueueMemberCallback(CallbackData, prefix="DeleteQueueMember"):
    messageID: int
    queueID: int


class RenameQueueCallback(CallbackData, prefix="RenameQueue"):
    queueID: int
    messageID: int


class SwapCallback(CallbackData, prefix="sp"):
    message_type: str
    first_user_id: int
    first_tg_user_id: int
    queueId: int
    second_user_id: int
    message2_id: int
    message1_id: int

class DeadLineAcceptCallback(CallbackData, prefix="da"):
    deadline_id: int
    user_id: int
    message_id: int
    solution: bool

class CanbanDesk(CallbackData, prefix="cd"):
    deadline_status_id: int
    is_done: bool
    message_id: int

class DeadStatus(CallbackData, prefix="ds"):
    deadline_status_id: int
    is_done: bool
    message_id: int
    d_type: str
    del_mes: int


class EditDeadline(CallbackData, prefix="ed"):
    deadline_id: int
    message_id: int


class QueueSwapPagination(CallbackData, prefix="qsp"):
    offset: int
    message_id: int

class QueuePagination(CallbackData, prefix="qp"):
    offset: int
    message_id: int


class DeadPagination(CallbackData, prefix="dp"):
    offset: int
    message_id: int


class EditDeadPagination(CallbackData, prefix="edp"):
    offset: int
    message_id: int


class RenameDeadlineCallback(CallbackData, prefix="rdc"):
    deadline_id: int


class DeleteDeadlineCallback(CallbackData, prefix="ddc"):
    deadline_id: int
    messageID: int


class ReturnToDeadlineList(CallbackData, prefix="rtl"):
    messageID: int
