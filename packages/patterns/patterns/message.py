from typing import Union, Protocol


class Message(Protocol):
    """
    Data type of message from queue

    ---

    Тип данных "Сообщение" для очереди
    """


class Command(Message):
    """
    Data type of command for queue

    ---

    Тип данных "Команда" для очереди
    """


class Event(Message):
    """
    Data type of event after sending message

    ---

    Тип данных "Событие" появляется после отправки "Сообщения"
    """


MessageType = Union[Command, Event]
