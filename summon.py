# Usage: python summon.py "title string" or python summon.py file.mrc
# Check if a title or set of MARC records is in Summon
# Code substantially based on Summon API Toolkit for Python 3
# https://github.com/summon/summon-api-toolkit/blob/master/python3/app/modules/summonapi.py
import argparse
import base64
import csv
from datetime import datetime
import hashlib
import hmac
import os
import re
import signal
import sys
import time
from typing import List
from urllib.parse import urlencode, quote_plus, unquote_plus

from dotenv import dotenv_values
from pymarc import Field, MARCReader, Record
import requests

config: dict = {
    **dotenv_values(".env"),  # load shared development variables
    **os.environ,  # override loaded values with environment variables
}
config["ACCEPT"] = "application/json"
config["PATH"] = "/2.0.0/search"

summary: dict[str, int] = {
    "Records": 0,
    "Found": 0,
    "Had ISBN": 0,
    "ISBN Matches": 0,
    "HTTP Errors": 0,
}


def build_auth_string(id_string: str) -> str:
    """
    Generates authentication string needed for Authorization header.

    Args:
        id_string (str): string from build_headers combining query, etc.

    Returns:
        string: "Summon your_access_id;base64_encoded_hash"
    """
    key: bytes = bytes(config["API_KEY"], "UTF-8")
    message: bytes = bytes(id_string, "UTF-8")
    hashed_code: bytes = hmac.new(key, message, hashlib.sha1).digest()
    digest: str = base64.encodebytes(hashed_code).decode("UTF-8")

    auth_string: str = "Summon {};{}".format(config["ACCESS_ID"], digest)
    return auth_string.replace("\n", "")


def build_headers(query) -> dict[str, str]:
    """
    Generates the request headers for the Summon API query.

    Args:
        query (dict): URL-encoded query, created from params by search function

    Returns:
        dict: request headers for Summon API query
    """
    date: str = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

    # sort and decode query
    query_string: str = unquote_plus("&".join(sorted(query.split("&"))))

    id_string: str = (
        "\n".join(
            [config["ACCEPT"], date, config["HOST"], config["PATH"], query_string]
        )
        + "\n"
    )

    auth_string: str = build_auth_string(id_string)

    return {
        "Accept": config["ACCEPT"],
        "x-summon-date": date,
        "Host": config["HOST"],
        "Authorization": auth_string,
    }


def encode_query(params) -> str:
    """
    Encodes the query parameters for the Summon API.

    Args:
        params (dict): Search parameters, sent as dictionary or list of tuples

    Returns:
        string: URL-encoded query string
    """
    return urlencode(params, doseq=True, quote_via=quote_plus)


def search_link(qs) -> str:
    """
    Generate a (clickable, non-API) search URL for Summon from a query string.

    Args:
        qs (str): URL-encoded query string from encode_query

    Returns:
        string: URL for Summon API search
    """
    return f"https://{config['ACCESS_ID']}.summon.serialssolutions.com/search?{qs}"


def search(params) -> list[dict]:
    """
    Searches the Summon API with the provided parameters.

    Args:
        params (dict): Search parameters, sent as dictionary or list of tuples

    Returns:
        dict: JSON response from Summon API containing search results, etc.
    """
    host: str = "api.summon.serialssolutions.com"
    path: str = "/2.0.0/search"
    qs: str = encode_query(params)

    headers: dict[str, str] = build_headers(qs)

    url: str = "https://{}{}?{}".format(host, path, qs)
    # print normal, non-API search URL for debugging
    if args.debug:
        print(search_link(qs))
    # Summon API connection errors are common
    # TODO retry with a delay in between?
    time.sleep(1)
    try:
        response: requests.Response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()["documents"]
    except requests.exceptions.ConnectionError as e:
        summary["HTTP Errors"] += 1
        print(f"Connection Error: {e}")
        print(f"Search URL: {search_link(qs)}")
        time.sleep(5)  # wait and keep going
        return []


def result(documents: list[dict]) -> None:
    """
    Print output/summary of search results.
    """
    print(f"Search Results: {len(documents)}")
    for doc in documents:
        print(f"Title: {re.sub(r'</?h>', '', doc.get('Title',[''])[0])}")
        print(f"Authors: {', '.join(doc.get('Author',['']))}")
        print(f"Publication Date: {doc.get('PublicationDate',[''])[0]}")
        print(f"ISBNs: {', '.join(doc.get('ISBN',['']))}")
        print(f"Type: {doc['ContentType'][0]}")
        print(
            f"Summon Link: https://{config['ACCESS_ID']}.summon.serialssolutions.com/search?bookMark={doc['BookMark'][0]}"
        )
        print("")


def get_first_author(record) -> str | None:
    """
    Get author from MARC record. Pymarc's record.author includes identifier &
    dates which messes up Summon query.
    """
    author: list[Field] = record.get_fields("100")
    if len(author):
        return author[0].get_subfields("a")[0]
    else:
        return None


def make_query(record: Record) -> dict[str, str]:
    """
    Create Summon query string from MARC record.
    """
    title: str | None = record.title  # technically can be None but not our data
    author: str | None = get_first_author(record)

    params: dict[str, str] = {
        "s.q": f"(TitleCombined:({title}))",
        "s.fvf": "SourceType,Library Catalog,f",
    }
    if author:
        params["s.q"] += f" AND (AuthorCombined:({author})) "
    return params


def summarize() -> None:
    print(
        f"""Total Records:      {summary["Records"]}
Had Search Results: {summary["Found"]}
Had ISBN:           {summary["Had ISBN"]}
ISBN Matches:       {summary["ISBN Matches"]}
HTTP Errors:        {summary["HTTP Errors"]}
"""
    )
    if summary.get("Malformed Records"):
        print(f"Malformed Records: {summary['Malformed Records']}")


def write_missing(missing) -> None:
    """
    Write missing records to CSV file.
    """
    if len(missing):
        with open(args.missing, "w") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "Biblionumber",
                    "Title",
                    "Author",
                    "ISBN",
                    "Koha Link",
                    "Summon Search",
                ]
            )
            for record in missing:
                # null for non-Koha records
                biblionumber: str | None = record.get("999", {}).get("c")
                qs: str = encode_query(make_query(record))
                writer.writerow(
                    [
                        biblionumber,
                        record.title,
                        get_first_author(record),
                        record.isbn,
                        f"https://{config['KOHA_DOMAIN']}/cgi-bin/koha/opac-detail.pl?biblionumber={biblionumber}",
                        search_link(qs),
                    ]
                )


def has_match(list1: list, list2: list) -> bool:
    """
    Check if any items in list1 are in list2.
    """
    return any(item in list1 for item in list2)


def num_only(isbn: str) -> str:
    """
    020$a ISBN fields often have a type or volume postfix
    "9780060638412 (v. 1-2)", "9780393050240 (hardcover)"
    Split on space and return first part.
    """
    return isbn.split(" ")[0]


def process_marc(file) -> None:
    """
    Parse MARC file and search for items.
    """
    missing: list[Record] = []
    reader = MARCReader(open(file, "rb"))
    for i, record in enumerate(reader):
        if args.count and i >= args.count:
            break
        if record:
            # skip suppressed records 942$n = 1
            try:
                suppressed: str = record.get_fields("942")[0].get_subfields("n")[0]
                if suppressed == "1" or suppressed.lower() == "true":
                    continue
            except IndexError:
                pass

            summary["Records"] += 1

            isbn_fields: List[Field] = record.get_fields("020")
            isbn_subfields: List[List[str]] = [
                field.get_subfields("a") for field in isbn_fields
            ]
            isbns: List[str] = [
                num_only(isbn) for sublist in isbn_subfields for isbn in sublist
            ]
            summary["Had ISBN"] += 1 if len(isbns) else 0

            params: dict[str, str] = make_query(record)
            docs: list[dict] = search(params)
            if args.debug:
                result(docs)

            summary["Found"] += 1 if len(docs) else 0
            if len(isbns):
                for doc in docs:
                    if has_match(doc.get("ISBN", []), isbns):
                        summary["ISBN Matches"] += 1
                        break
                else:
                    if args.missing:
                        missing.append(record)

        else:
            summary["Malformed Records"] += 1

    summarize()
    if args and args.missing:
        write_missing(missing)


def quote_if_unquoted(s: str) -> str:
    """
    Quote string if it's not already quoted.
    """
    if s.startswith('"') and s.endswith('"'):
        return s
    else:
        return f'"{s}"'


def signal_handler(sig, frame) -> None:
    print("Caught SIGINT, printing summary")
    summarize()
    sys.exit(1)


def main() -> None:
    # if cli arg looks like a MARC file, parse it & search for items
    # otherwise treat as a title string for search
    if args.query.endswith(".mrc") or args.query.endswith(".marc"):
        process_marc(args.query)
    elif len(args.query) > 0:
        params = {
            "s.q": f"{quote_if_unquoted(args.query)}",
            "s.fvf": ["SourceType,Library Catalog,f"],
        }
        result(search(params))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find items in Summon")
    parser.add_argument(
        "query",
        metavar="<file.mrc or title string>",
        type=str,
        help="Title or MARC file to search for",
    )
    parser.add_argument("-c", "--count", type=int, help="Number of searches to run")
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Debug mode (print query links and search results)",
    )
    parser.add_argument(
        "-m", "--missing", help="write list of missing records to CSV file"
    )
    global args
    args: argparse.Namespace = parser.parse_args()

    # catch SIGINT and print summary
    signal.signal(signal.SIGINT, signal_handler)
    main()
