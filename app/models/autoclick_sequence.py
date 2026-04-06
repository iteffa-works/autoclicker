"""Serializable steps for sequence autoclick mode."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class AutoclickSequenceStepType(str, Enum):
    DELAY = "delay"
    KEY_DOWN = "key_down"
    KEY_UP = "key_up"
    MOUSE_CLICK = "mouse_click"


@dataclass
class AutoclickSequenceStep:
    type: AutoclickSequenceStepType
    key: str = ""
    button: str = "left"
    delay_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type.value,
            "key": self.key,
            "button": self.button,
            "delay_ms": self.delay_ms,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AutoclickSequenceStep:
        t = str(data.get("type", "delay")).lower()
        try:
            st = AutoclickSequenceStepType(t)
        except ValueError:
            st = AutoclickSequenceStepType.DELAY
        return cls(
            type=st,
            key=str(data.get("key", "")),
            button=str(data.get("button", "left")),
            delay_ms=float(data.get("delay_ms", 0.0)),
        )


class SequenceRepeatMode(str, Enum):
    FULL = "full"
    SINGLE_STEP = "single_step"
