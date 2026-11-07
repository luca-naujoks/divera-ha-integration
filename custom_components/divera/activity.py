"""Persistent alarm activity, independent of Home Assistant's entity lifecycle."""

from __future__ import annotations

from dataclasses import asdict, dataclass


def alarm_bool(value: object) -> bool | None:
    """Normalize API booleans without treating the string '0' as true."""
    if value in (True, 1, "1", "true"):
        return True
    if value in (False, 0, "0", "false"):
        return False
    return None


@dataclass
class AlarmActivity:
    """Remember the last alarm even after its timer expires or it disappears."""

    alarm_id: str | None = None
    started_at: float | None = None
    expires_at: float | None = None

    @classmethod
    def restore(cls, data: dict | None, minutes: int) -> AlarmActivity:
        """Restore a deadline; apply changed options relative to the original start."""
        if not data:
            return cls()
        alarm_id = data.get("alarm_id")
        started_at = data.get("started_at")
        expires_at = data.get("expires_at")
        if not isinstance(alarm_id, str) or not isinstance(started_at, (int, float)):
            return cls()
        return cls(
            alarm_id=alarm_id,
            started_at=started_at,
            expires_at=started_at + minutes * 60 if expires_at is not None else None,
        )

    def update(self, alarm: dict | None, now: float, minutes: int) -> bool:
        """Start only for a new alarm ID; close/remove cancels the current timer."""
        previous = self.as_dict()
        if alarm is None or alarm.get("id") is None:
            self.expires_at = None
            return previous != self.as_dict()

        alarm_id = str(alarm["id"])
        if alarm_id != self.alarm_id:
            self.alarm_id = alarm_id
            self.started_at = now
            self.expires_at = now + minutes * 60

        if alarm_bool(alarm.get("closed")) is True:
            self.expires_at = None
        return previous != self.as_dict()

    def is_active(self, now: float) -> bool:
        """An elapsed deadline remains stored to prevent accidental reactivation."""
        return self.expires_at is not None and now < self.expires_at

    def as_dict(self) -> dict:
        """Return JSON-compatible persistent data."""
        return asdict(self)
