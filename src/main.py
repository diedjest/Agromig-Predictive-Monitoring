import os
import time
import logging
from models import GrainProfile, AlertSeverity
from emulator import HardwareEmulator
from processing import SignalProcessor, DecisionEngine
from database import DatabaseManager

DB_DSN = os.getenv(
    "AGROMIG_DB_DSN", "dbname=agromig_db user=postgres password=pass host=localhost"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("AgromigCore")


class MonitoringSystem:
    def __init__(self, profile: GrainProfile, db: DatabaseManager):
        self.emulator = HardwareEmulator(profile=profile)
        self.processor = SignalProcessor()
        self.engine = DecisionEngine(profile=profile)
        self.db = db
        self.is_running = True

        profile_id = self.db.get_profile_id(profile.crop_name)
        self.session_id = self.db.start_session(profile_id)
        logger.info(f"Monitoring session started. ID: {self.session_id}")

    def run_step(self):
        raw_reading = self.emulator.read_sensors()
        clean_reading = self.processor.process(raw_reading)

        self.db.log_reading(self.session_id, clean_reading)

        logger.info(
            f"Metrics -> Temp: {clean_reading.temperature}C | Moisture: {clean_reading.moisture_out}%"
        )

        alert = self.engine.evaluate(clean_reading)
        if alert:
            self.db.log_alert(self.session_id, alert)

            log_level = (
                logging.WARNING
                if alert.severity != AlertSeverity.SUCCESS
                else logging.INFO
            )
            logger.log(
                log_level,
                f"[{alert.severity.value}] {alert.message} -> Action: {alert.action_required}",
            )

            if alert.severity == AlertSeverity.SUCCESS:
                logger.info("Process completed successfully.")
                self.db.finish_session(self.session_id)
                self.is_running = False


def main():
    db = DatabaseManager(DB_DSN)
    try:
        db.connect()
        profile = GrainProfile(
            crop_name="Wheat", optimal_temp=45.0, max_temp=55.0, target_moisture=14.0
        )
        system = MonitoringSystem(profile, db)

        while system.is_running:
            system.run_step()
            time.sleep(1)

    except Exception as e:
        logger.error(f"Critical failure: {e}")
    finally:
        db.close()
        logger.info("Service stopped.")


if __name__ == "__main__":
    main()
