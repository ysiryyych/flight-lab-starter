"""Row validation: airport list loading, single-row checks, record building."""
import math
import re
from datetime import datetime

FLIGHT_ID_RE = re.compile(r"[A-Za-z0-9]{2,8}", re.ASCII)
AIRPORT_RE = re.compile(r"[A-Z]{3}", re.ASCII)
DATETIME_RE = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", re.ASCII)
DATETIME_FORMAT = "%Y-%m-%d %H:%M"


def load_airports(path: str) -> set[str]:
    """Read an airport list file and return the set of codes.

    One code per line. Strip whitespace; skip blank lines and lines
    starting with '#'.
    """
    airports = set()
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            code = line.strip()
            if not code or code.startswith("#"):
                continue
            airports.add(code)
    return airports


def parse_datetime(text: str) -> datetime | None:
    """Return a datetime if text is exactly 'YYYY-MM-DD HH:MM', else None."""
    if not DATETIME_RE.fullmatch(text):
        return None
    try:
        return datetime.strptime(text, DATETIME_FORMAT)
    except ValueError:
        return None


def _valid_airport(code: str, airports: set[str]) -> bool:
    return bool(AIRPORT_RE.fullmatch(code)) and code in airports


def validate_row(fields: list[str], airports: set[str]) -> str | None:
    """Check one CSV row (fields as returned by csv.reader, not yet stripped).

    Return None if the row is valid, otherwise the error code of the
    FIRST failing check (checks 1-11 in the specification, in order).
    Does not check for duplicates.
    """
  
    if len(fields) != 6:
        return "WRONG_FIELD_COUNT"

    flight_id, origin, destination, departure, arrival, price = (f.strip() for f in fields)


    if not all((flight_id, origin, destination, departure, arrival, price)):
        return "MISSING_FIELD"


    if not FLIGHT_ID_RE.fullmatch(flight_id):
        return "INVALID_FLIGHT_ID"


    if not _valid_airport(origin, airports):
        return "INVALID_ORIGIN"
    if not _valid_airport(destination, airports):
        return "INVALID_DESTINATION"


    if origin == destination:
        return "SAME_ORIGIN_DESTINATION"


    dep = parse_datetime(departure)
    if dep is None:
        return "INVALID_DEPARTURE"
    arr = parse_datetime(arrival)
    if arr is None:
        return "INVALID_ARRIVAL"

    # 9. order of times
    if arr <= dep:
        return "ARRIVAL_NOT_AFTER_DEPARTURE"


    try:
        value = float(price)
    except ValueError:
        return "INVALID_PRICE"
    if not math.isfinite(value):
        return "INVALID_PRICE"
    if value <= 0:
        return "NON_POSITIVE_PRICE"

    return None


def to_record(fields: list[str]) -> dict:
    """Turn a valid row into a flight record dictionary.

    Keys: flight_id, origin, destination, departure_datetime,
    arrival_datetime (stripped strings) and price (float).
    """
    flight_id, origin, destination, departure, arrival, price = (f.strip() for f in fields)
    return {
        "flight_id": flight_id,
        "origin": origin,
        "destination": destination,
        "departure_datetime": departure,
        "arrival_datetime": arrival,
        "price": float(price),
    }