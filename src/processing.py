import math
from typing import List, Optional
from models import SensorReading, GrainProfile, Alert, AlertSeverity


class SignalProcessor:
    ENTROPY_THRESHOLD = 5.0

    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self._temp_buffer: List[float] = []
        self._ema_temp: Optional[float] = None

    def _calculate_shannon_entropy(self, data: List[float]) -> float:
        if not data:
            return 0.0
        hist = {}
        for val in data:
            bin_val = round(val)
            hist[bin_val] = hist.get(bin_val, 0) + 1

        entropy = 0.0
        total = len(data)
        for count in hist.values():
            prob = count / total
            if prob > 0:
                entropy -= prob * math.log2(prob)
        return entropy

    def process(self, reading: SensorReading) -> SensorReading:
        self._temp_buffer.append(reading.temperature)
        if len(self._temp_buffer) > self.window_size:
            self._temp_buffer.pop(0)

        entropy = self._calculate_shannon_entropy(self._temp_buffer)
        alpha = max(0.1, min(0.9, 1.0 - (entropy / self.ENTROPY_THRESHOLD)))

        if self._ema_temp is None:
            self._ema_temp = reading.temperature
        else:
            self._ema_temp = alpha * reading.temperature + (1 - alpha) * self._ema_temp

        return SensorReading(
            temperature=round(self._ema_temp, 2),
            moisture_in=reading.moisture_in,
            moisture_out=reading.moisture_out,
            timestamp=reading.timestamp,
        )


class DecisionEngine:
    TEMP_TOLERANCE = 2.0

    def __init__(self, profile: GrainProfile):
        self.profile = profile
        self.batch_ready = False

    def evaluate(self, reading: SensorReading) -> Optional[Alert]:
        if reading.moisture_out <= self.profile.target_moisture:
            self.batch_ready = True
            return Alert(
                severity=AlertSeverity.SUCCESS,
                message=f"Target reached: Moisture {reading.moisture_out}% meets requirement ({self.profile.target_moisture}%)",
                action_required="Initialize batch discharge sequence. Grain ready for storage.",
            )

        if reading.temperature >= self.profile.max_temp:
            return Alert(
                severity=AlertSeverity.CRITICAL,
                message=f"Thermal limit violation: Core temperature {reading.temperature}C exceeds {self.profile.max_temp}C",
                action_required="Initiate emergency cooling: Increase conveyor velocity by 15%",
            )

        if reading.temperature > self.profile.optimal_temp + self.TEMP_TOLERANCE:
            return Alert(
                severity=AlertSeverity.WARNING,
                message=f"Temperature {reading.temperature}C exceeds optimal range",
                action_required="Adjustment required: Increase conveyor velocity by 5%",
            )

        if reading.temperature < self.profile.optimal_temp - self.TEMP_TOLERANCE:
            return Alert(
                severity=AlertSeverity.INFO,
                message=f"Temperature {reading.temperature}C is below optimal range",
                action_required="Adjustment required: Decrease conveyor velocity by 5%",
            )

        return None
