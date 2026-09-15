from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class AlertSeverity(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    SUCCESS = "SUCCESS"


@dataclass
class SensorReading:
    temperature: float
    moisture_in: float
    moisture_out: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class GrainProfile:
    crop_name: str
    optimal_temp: float
    max_temp: float
    target_moisture: float

    def __post_init__(self):
        if self.max_temp <= self.optimal_temp:
            raise ValueError(
                f"Configuration error: Max temperature ({self.max_temp}) must exceed optimal ({self.optimal_temp})"
            )
        if not (0 < self.target_moisture < 100):
            raise ValueError(
                "Configuration error: Target moisture must be in range (0, 100)"
            )


@dataclass
class Alert:
    severity: AlertSeverity
    message: str
    action_required: str
    timestamp: datetime = field(default_factory=datetime.now)
