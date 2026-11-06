import logging
from pathlib import Path
from tortalk.config import resolve_config_dir

def setup_logging(config_dir: str | Path | None = None, profile: str | None = None) -> Path:
    cfg_dir = resolve_config_dir(config_dir, profile)
    cfg_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    log_file = cfg_dir / "debug.log"
    
    # Overwrite on start (mode 'w')
    handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] [%(name)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    # Remove existing handlers to avoid duplicates
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
    root_logger.addHandler(handler)
    
    # Quiet noisy external libraries
    logging.getLogger("stem").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    logger = logging.getLogger("tork")
    logger.info(f"Tork logging initialized at {log_file}. Log file cleared for new session.")
    return log_file
