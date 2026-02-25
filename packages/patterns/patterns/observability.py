from typing import Iterable, Protocol, Any
from .message import Command, Event


class ObservabilityHook(Protocol):
    """
    ObservabilityHook - он внедряет хуки наблюдаемости в архитектуру Command / Event / UoW
    - логи
    - метрики
    - трассировки
    - мониторинг
    - алерты
    """

    async def on_command_start(self, cmd: Command) -> None: ...
    async def on_command_end(self, cmd: Command, result: Any | None) -> None: ...
    async def on_command_error(self, cmd: Command, err: BaseException) -> None: ...

    async def on_event_start(self, evt: Event) -> None: ...
    async def on_event_end(self, evt: Event) -> None: ...
    async def on_event_error(self, evt: Event, err: BaseException) -> None: ...

    async def on_uow_commit(self) -> None: ...
    async def on_uow_rollback(self) -> None: ...


class NoopHook:
    """
    Это “пустой” хук он позволяет всегда передать NoopHook и не думать о None
    """

    async def on_command_start(self, cmd: Command) -> None: ...
    async def on_command_end(self, cmd: Command, result: Any | None) -> None: ...
    async def on_command_error(self, cmd: Command, err: BaseException) -> None: ...
    async def on_event_start(self, evt: Event) -> None: ...
    async def on_event_end(self, evt: Event) -> None: ...
    async def on_event_error(self, evt: Event, err: BaseException) -> None: ...
    async def on_uow_commit(self) -> None: ...
    async def on_uow_rollback(self) -> None: ...


class CompositeHook:
    """
    Позволяет объединять несколько хуков
    """

    def __init__(self, *hooks: ObservabilityHook) -> None:
        self._hooks: Iterable[ObservabilityHook] = hooks

    async def on_command_start(self, cmd: Command) -> None:
        for hook in self._hooks:
            await hook.on_command_start(cmd=cmd)

    async def on_command_end(self, cmd: Command, result: Any | None) -> None:
        for hook in self._hooks:
            await hook.on_command_end(cmd=cmd, result=result)

    async def on_command_error(self, cmd: Command, err: BaseException) -> None:
        for hook in self._hooks:
            await hook.on_command_error(cmd=cmd, err=err)

    async def on_event_start(self, evt: Event) -> None:
        for hook in self._hooks:
            await hook.on_event_start(evt=evt)

    async def on_event_end(self, evt: Event) -> None:
        for hook in self._hooks:
            await hook.on_event_end(evt=evt)

    async def on_event_error(self, evt: Event, err: BaseException) -> None:
        for hook in self._hooks:
            await hook.on_event_error(evt=evt, err=err)

    async def on_uow_commit(self) -> None:
        for hook in self._hooks:
            await hook.on_uow_commit()

    async def on_uow_rollback(self) -> None:
        for hook in self._hooks:
            await hook.on_uow_rollback()
