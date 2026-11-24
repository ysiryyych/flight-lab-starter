"""Running queries against the flight database."""
import math

from validator import parse_datetime

RECORD_KEYS = ("flight_id", "origin", "destination",
               "departure_datetime", "arrival_datetime", "price")
STRING_KEYS = ("flight_id", "origin", "destination")
DATETIME_KEYS = ("departure_datetime", "arrival_datetime")
NUMBER_KEYS = ("price", "min_price")
ALLOWED_KEYS = set(STRING_KEYS) | set(DATETIME_KEYS) | set(NUMBER_KEYS) | {"sort_by", "order", "limit"}


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _query_is_valid(query) -> bool:
    if not isinstance(query, dict):
        return False
    if not set(query) <= ALLOWED_KEYS:
        return False
    for key in STRING_KEYS:
        if key in query and not isinstance(query[key], str):
            return False
    for key in DATETIME_KEYS:
        if key in query:
            value = query[key]
            if not isinstance(value, str) or parse_datetime(value) is None:
                return False
    for key in NUMBER_KEYS:
        if key in query and not _is_number(query[key]):
            return False
    if "sort_by" in query and query["sort_by"] not in RECORD_KEYS:
        return False
    if "order" in query:
        if query["order"] not in ("asc", "desc") or "sort_by" not in query:
            return False
    if "limit" in query:
        limit = query["limit"]
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 0:
            return False
    return True


def _matches(record: dict, query: dict) -> bool:
    for key in STRING_KEYS:
        if key in query and record[key] != query[key]:
            return False
    if "departure_datetime" in query and record["departure_datetime"] < query["departure_datetime"]:
        return False
    if "arrival_datetime" in query and record["arrival_datetime"] > query["arrival_datetime"]:
        return False
    if "price" in query and not record["price"] <= query["price"]:
        return False
    if "min_price" in query and not record["price"] >= query["min_price"]:
        return False
    return True


def run_query(db: list[dict], query: dict) -> dict:
    """Return one response entry for one query object.

    Valid query:   {"query": query, "matches": [...]}
    Invalid query: {"query": query, "error": "INVALID_QUERY", "matches": []}
    """
    if not _query_is_valid(query):
        return {"query": query, "error": "INVALID_QUERY", "matches": []}

    found = [record for record in db if _matches(record, query)]
    if "sort_by" in query:
        found = sorted(found, key=lambda r: r[query["sort_by"]],
                       reverse=query.get("order", "asc") == "desc")
    if "limit" in query:
        found = found[:query["limit"]]
    return {"query": query, "matches": found}


def run_queries(db: list[dict], queries: dict | list) -> list[dict]:
    """Accept one query object or a list of them; always return a list."""
    if not isinstance(queries, list):
        queries = [queries]
    return [run_query(db, q) for q in queries]