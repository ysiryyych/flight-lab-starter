"""Flight schedule parser and query tool (command-line entry point)."""
import argparse
import json
import logging
import os
import sys
from datetime import datetime

from csv_loader import parse_files
from query import run_queries
from validator import load_airports

# TODO: replace the placeholder ID with your own: plain ASCII, no spaces or underscores.
STUDENT_ID = "251ADB151"
FIRST_NAME = "Yaroslava"
LAST_NAME = "Sirychenko"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flight_parser.py",
        description="Validate flight CSV files, store valid flights as JSON and answer queries.",
        allow_abbrev=False,
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("-i", metavar="FILE", help="parse a single CSV file")
    source.add_argument("-d", metavar="FOLDER", help="parse every .csv file in a folder")
    source.add_argument("-j", metavar="FILE", help="load an existing JSON database")
    parser.add_argument("-a", metavar="FILE", help="airport list file (required with -i and -d)")
    parser.add_argument("-o", metavar="FILE", help="output path for the JSON database (default: db.json)")
    parser.add_argument("-q", metavar="FILE", help="JSON file with queries to run")
    parser.add_argument("-r", metavar="FOLDER", default=".", help="folder for the query response file")
    return parser


def read_json(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def csv_paths_in(folder: str) -> list[str]:
    if not os.path.isdir(folder):
        raise OSError(f"folder not found: {folder}")
    names = sorted(n for n in os.listdir(folder)
                   if n.endswith(".csv") and os.path.isfile(os.path.join(folder, n)))
    if not names:
        raise OSError(f"no .csv files in folder: {folder}")
    return [os.path.join(folder, n) for n in names]


def write_database_and_log(records: list[dict], errors: list[str], db_path: str) -> None:
    log_path = os.path.join(os.path.dirname(os.path.abspath(db_path)), "errors.log")
    logger = logging.getLogger("flight_parser")
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(handler)
    try:
        for message in errors:
            logger.warning("%s", message)
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
    finally:
        logger.removeHandler(handler)
        handler.close()


def run(args) -> None:
    if args.j:
        db = read_json(args.j)
        if not isinstance(db, list) or not all(isinstance(r, dict) for r in db):
            raise ValueError(f"{args.j} must contain a JSON array of objects")
    else:
        airports = load_airports(args.a)
        paths = [args.i] if args.i else csv_paths_in(args.d)
        db, errors = parse_files(paths, airports)
        write_database_and_log(db, errors, args.o or "db.json")
        print(f"{len(db)} valid flights, {len(errors)} invalid rows")

    if args.q:
        queries = read_json(args.q)
        if not isinstance(queries, (dict, list)):
            raise ValueError(f"{args.q} must contain a query object or an array of them")
        response = run_queries(db, queries)
        stamp = datetime.now().strftime("%Y%m%d_%H%M")
        name = f"response_{STUDENT_ID}_{FIRST_NAME}_{LAST_NAME}_{stamp}.json"
        with open(os.path.join(args.r, name), "w", encoding="utf-8") as f:
            json.dump(response, f, indent=2)


def main(argv: list[str] | None = None) -> int:
    """Run the whole program and return the exit code (0, 1 or 2).

    argv is the argument list without the program name.
    None means use sys.argv[1:] (argparse does this for you).
    Do not call sys.exit() inside main(); return the code instead.
    """
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        if (args.i or args.d) and not args.a:
            parser.error("-a is required with -i and -d")
        if args.j and args.o:
            parser.error("-o cannot be used with -j")
    except SystemExit as exit_request:
        code = exit_request.code
        return code if isinstance(code, int) else (0 if code is None else 2)

    try:
        run(args)
    except (OSError, ValueError) as problem:
        message = str(problem).replace("\n", " ")
        print(f"Error: {message}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())