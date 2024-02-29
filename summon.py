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
import sys
import time
from urllib.parse import urlencode, quote_plus, unquote_plus

from dotenv import dotenv_values
from pymarc import MARCReader
import requests

config = {
    **dotenv_values(".env"),  # load shared development variables
    **os.environ,  # override loaded values with environment variables
}
config["ACCEPT"] = "application/json"
config["PATH"] = "/2.0.0/search"

summary = {
    "Records": 0,
    "Found": 0,
    "Had ISBN": 0,
    "ISBN Matches": 0,
}


def build_auth_string(id_string) -> str:
    """
    Generates authentication string needed for Authorization header.

    Args:
        id_string (str): string from build_headers combining query, etc.

    Returns:
        string: "Summon your_access_id;base64_encoded_hash"
    """
    key = bytes(config["API_KEY"], "UTF-8")
    message = bytes(id_string, "UTF-8")
    hashed_code = hmac.new(key, message, hashlib.sha1).digest()
    digest = base64.encodebytes(hashed_code).decode("UTF-8")

    auth_string = "Summon {};{}".format(config["ACCESS_ID"], digest)
    return auth_string.replace("\n", "")


def build_headers(query) -> dict[str, str]:
    """
    Generates the request headers for the Summon API query.

    Args:
        query (dict): URL-encoded query, created from params by search function

    Returns:
        dict: request headers for Summon API query
    """
    date = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

    # sort and decode query
    query_string = unquote_plus("&".join(sorted(query.split("&"))))

    id_string = (
        "\n".join(
            [config["ACCEPT"], date, config["HOST"], config["PATH"], query_string]
        )
        + "\n"
    )

    auth_string = build_auth_string(id_string)

    return {
        "Accept": config["ACCEPT"],
        "x-summon-date": date,
        "Host": config["HOST"],
        "Authorization": auth_string,
    }


def search(params):
    """
    Searches the Summon API with the provided parameters.

    Args:
        params (dict): Search parameters, sent as dictionary or list of tuples

    Returns:
        dict: JSON response from Summon API containing search results, etc.
    """
    host = "api.summon.serialssolutions.com"
    path = "/2.0.0/search"
    query = urlencode(params, doseq=True, quote_via=quote_plus)

    headers = build_headers(query)

    url = "https://{}{}?{}".format(host, path, query)
    # print normal, non-API search URL for debugging
    if args.debug:
        print(
            f"https://{config['ACCESS_ID']}.summon.serialssolutions.com/search?{query}"
        )
    # ! sometimes fails with connection error, not even at particularly high volume
    time.sleep(1)
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except:
        print(f"Error: {sys.exc_info()[0]}")
        print(f"Search URL: {url}")
        time.sleep(5)  # wait and keep going
        return {"documents": []}


def result(documents):
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


def get_first_author(record):
    """
    Get author from MARC record. Pymarc's record.author includes identifier &
    dates which messes up Summon query.
    """
    author = record.get_fields("100")
    if len(author):
        return author[0].get_subfields("a")[0]
    else:
        return None


def make_query(record) -> dict[str, str]:
    """
    Create Summon query string from MARC record.
    """
    title = record.title
    author = get_first_author(record)

    params = {
        "s.q": f"(TitleCombined:({title}))",
        "s.fvf": "SourceType,Library Catalog,f",
    }
    if author:
        params["s.q"] += f" AND (AuthorCombined:({author})) "
    return params


def summarize():
    print(
        f"""Total Records:      {summary["Records"]}
Had Search Results: {summary["Found"]}
Had ISBN:           {summary["Had ISBN"]}
ISBN Matches:       {summary["ISBN Matches"]}
"""
    )
    if summary.get("Malformed Records"):
        print(f"Malformed Records: {summary['Malformed Records']}")


def write_missing(missing):
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
                biblionumber = record.get("999", {}).get("c")
                qs = urlencode(make_query(record), doseq=True, quote_via=quote_plus)
                writer.writerow(
                    [
                        biblionumber,
                        record.title,
                        get_first_author(record),
                        record.isbn,
                        f"https://library.cca.edu/cgi-bin/koha/opac-detail.pl?biblionumber={biblionumber}",
                        f"https://{config['ACCESS_ID']}.summon.serialssolutions.com/search?{qs}",
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


def process_marc(file):
    """
    Parse MARC file and search for items.
    """
    missing = []
    reader = MARCReader(open(file, "rb"))
    for i, record in enumerate(reader):
        if args.count and i >= args.count:
            break
        if record:
            summary["Records"] += 1

            isbn_fields = record.get_fields("020")
            isbn_subfields = [field.get_subfields("a") for field in isbn_fields]
            isbns = [num_only(isbn) for sublist in isbn_subfields for isbn in sublist]
            if len(isbns):
                summary["Had ISBN"] += 1

            params = make_query(record)
            docs = search(params)["documents"]
            if args.debug:
                result(docs)

            if len(docs):
                summary["Found"] += 1
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


def quote_if_unquoted(s):
    """
    Quote string if it's not already quoted.
    """
    if s.startswith('"') and s.endswith('"'):
        return s
    else:
        return f'"{s}"'


def main():
    # if cli arg looks like a MARC file, parse it & search for items
    # otherwise treat as a title string for search
    if args.query.endswith(".mrc") or args.query.endswith(".marc"):
        process_marc(args.query)
    elif len(args.query) > 0:
        params = {
            "s.q": f"{quote_if_unquoted(args.query)}",
            "s.fvf": ["SourceType,Library Catalog,f"],
        }
        result(search(params)["documents"])


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
    args = parser.parse_args()
    main()
