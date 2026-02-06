from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Tuple

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(exist_ok=True)
LOG_FILE = DATA_DIR / "scraper.log"
DB_FILE = DATA_DIR / "aircrafts.db"

@dataclass
class ScraperConfig:
    base_url: str
    db_path: str
    max_retries: int = 3
    timeout: Tuple[int, int] = (10, 15)
    min_delay: float =  2.0
    max_delay: float = 5.0 
    max_errors_per_page: int = 5
    max_consecutive_failures: int = 3


    logging.basicConfig( 
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers = [
            logging.FileHandler(str(LOG_FILE)),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger(__name__)    