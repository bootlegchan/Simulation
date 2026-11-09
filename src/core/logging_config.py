"""Controlled, channel-based simulation logging."""
from enum import Enum
from typing import Any, Dict, List, Optional, Set

class LogMode(Enum):
    OFF = "OFF"
    CONSOLE = "CONSOLE"
    EVENTS = "EVENTS"
    BIOGRAPHICAL = "BIOGRAPHICAL"
    DIAGNOSTIC = "DIAGNOSTIC"
    ALL = "ALL"

class LogChannel(Enum):
    CONSOLE = "CONSOLE"
    DOMAIN_EVENTS = "DOMAIN_EVENTS"
    BIOGRAPHICAL = "BIOGRAPHICAL"
    DIAGNOSTIC = "DIAGNOSTIC"
    ACTIONS = "ACTIONS"
    INTERNAL_RECORDS = "INTERNAL_RECORDS"

class SimulationLogManager:
    """Singleton/Instance simulation logging manager."""
    _global_instance: Optional["SimulationLogManager"] = None

    def __init__(self, enabled: bool = False, mode: LogMode = LogMode.OFF, active_channels: Optional[Set[LogChannel]] = None):
        self.enabled = enabled
        self.mode = mode
        self.active_channels: Set[LogChannel] = set(active_channels or set())
        self.max_biographical_entries_per_npc: int = 50
        self.max_event_history: int = 2000

    @classmethod
    def get_global_instance(cls) -> "SimulationLogManager":
        if cls._global_instance is None:
            cls._global_instance = cls(enabled=False, mode=LogMode.OFF, active_channels=set())
        return cls._global_instance

    @classmethod
    def set_global_instance(cls, instance: "SimulationLogManager") -> None:
        cls._global_instance = instance

    def set_mode(self, mode: LogMode) -> None:
        self.mode = mode
        if mode == LogMode.OFF:
            self.enabled = False
            self.active_channels.clear()
        elif mode == LogMode.CONSOLE:
            self.enabled = True
            self.active_channels = {LogChannel.CONSOLE}
        elif mode == LogMode.EVENTS:
            self.enabled = True
            self.active_channels = {LogChannel.DOMAIN_EVENTS}
        elif mode == LogMode.BIOGRAPHICAL:
            self.enabled = True
            self.active_channels = {LogChannel.BIOGRAPHICAL}
        elif mode == LogMode.DIAGNOSTIC:
            self.enabled = True
            self.active_channels = {LogChannel.DIAGNOSTIC}
        elif mode == LogMode.ALL:
            self.enabled = True
            self.active_channels = set(LogChannel)

    def configure(self, mode: LogMode = LogMode.OFF, channels: Optional[Set[LogChannel]] = None) -> None:
        self.set_mode(mode)
        if channels is not None:
            self.active_channels = set(channels)
            self.enabled = len(self.active_channels) > 0

    def enable_channel(self, channel: Any) -> None:
        if isinstance(channel, str):
            channel = LogChannel[channel.upper()]
        self.active_channels.add(channel)
        self.enabled = True

    def disable_channel(self, channel: Any) -> None:
        if isinstance(channel, str):
            channel = LogChannel[channel.upper()]
        self.active_channels.discard(channel)
        if not self.active_channels:
            self.enabled = False

    def is_channel_enabled(self, channel: LogChannel) -> bool:
        return self.enabled and (channel in self.active_channels or LogChannel.ALL in self.active_channels)

    def log_console(self, msg: str) -> None:
        if self.is_channel_enabled(LogChannel.CONSOLE):
            print(msg)
