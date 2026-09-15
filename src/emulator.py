import random
from typing import NamedTuple
from models import GrainProfile, SensorReading


class SimulationState(NamedTuple):
    dm_dt: float
    dtg_dt: float


class HardwareEmulator:
    K_BASE = 0.002
    K_TEMP_COEFF = 0.0001
    HEAT_TRANSFER_COEFF = 0.05
    LATENT_HEAT_VAPOR = 3.0

    TEMP_MAX_LIMIT = 80.0
    TEMP_MIN_LIMIT = 20.0
    HEATING_STEP = 2.0
    COOLING_STEP = 3.0

    NOISE_TEMP = 2.5
    NOISE_MOISTURE_IN = 1.5
    NOISE_MOISTURE_OUT = 0.5

    def __init__(self, profile: GrainProfile):
        self.profile = profile
        self._M = profile.target_moisture + 6.0
        self._Tg = 20.0
        self._Ta = 65.0
        self._M_eq = profile.target_moisture - 2.0
        self._is_heating = True

    def _derivatives(self, M: float, Tg: float, Ta: float) -> SimulationState:
        k = self.K_BASE + self.K_TEMP_COEFF * Tg
        dm_dt = -k * (M - self._M_eq) if M > self._M_eq else 0.0
        dtg_dt = self.HEAT_TRANSFER_COEFF * (Ta - Tg) + self.LATENT_HEAT_VAPOR * dm_dt
        return SimulationState(dm_dt, dtg_dt)

    def _runge_kutta_4(self, dt: float = 1.0):
        M, Tg, Ta = self._M, self._Tg, self._Ta

        d1 = self._derivatives(M, Tg, Ta)
        d2 = self._derivatives(M + 0.5 * dt * d1.dm_dt, Tg + 0.5 * dt * d1.dtg_dt, Ta)
        d3 = self._derivatives(M + 0.5 * dt * d2.dm_dt, Tg + 0.5 * dt * d2.dtg_dt, Ta)
        d4 = self._derivatives(M + dt * d3.dm_dt, Tg + dt * d3.dtg_dt, Ta)

        self._M += (dt / 6.0) * (d1.dm_dt + 2 * d2.dm_dt + 2 * d3.dm_dt + d4.dm_dt)
        self._Tg += (dt / 6.0) * (d1.dtg_dt + 2 * d2.dtg_dt + 2 * d3.dtg_dt + d4.dtg_dt)

    def read_sensors(self) -> SensorReading:
        if self._Tg >= self.profile.max_temp + 1.0:
            self._is_heating = False
        elif self._Tg <= self.profile.optimal_temp - 2.0:
            self._is_heating = True

        if self._is_heating:
            self._Ta = min(self._Ta + self.HEATING_STEP, self.TEMP_MAX_LIMIT)
        else:
            self._Ta = max(self._Ta - self.COOLING_STEP, self.TEMP_MIN_LIMIT)

        self._runge_kutta_4(dt=2.0)

        return SensorReading(
            temperature=round(
                self._Tg + random.uniform(-self.NOISE_TEMP, self.NOISE_TEMP), 2
            ),
            moisture_in=round(
                (self.profile.target_moisture + 6.0)
                + random.uniform(-self.NOISE_MOISTURE_IN, self.NOISE_MOISTURE_IN),
                2,
            ),
            moisture_out=round(
                self._M
                + random.uniform(-self.NOISE_MOISTURE_OUT, self.NOISE_MOISTURE_OUT),
                2,
            ),
        )
