import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logger():
    logger = logging.getLogger("fastapi_app")
    logger.setLevel(logging.INFO)

    # Prevent duplicate logs if setup_logger is called multiple times
    if not logger.handlers:
        # Resolve logs path: backend/app/utils -> project_root/logs
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        log_dir = project_root / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "app.log"

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # 1. File Handler (Rotates at 5MB, keeps 5 backup files)
        file_handler = RotatingFileHandler(
            str(log_file), maxBytes=5 * 1024 * 1024, backupCount=5
        )
        file_handler.setFormatter(formatter)

        # 2. Console Handler (To see logs in terminal)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Return a child logger for the given module (e.g. __name__)."""
    return logging.getLogger("fastapi_app" if name == "__main__" else f"fastapi_app.{name}")


# Main app logger (use this or get_logger(__name__) in modules)
logger = setup_logger()
