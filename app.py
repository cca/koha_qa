# Code substantially based on Summon API Toolkit for Python 3
# https://github.com/summon/summon-api-toolkit/blob/master/python3/app/modules/summonapi.py
import base64
from datetime import datetime
import hashlib
import hmac
import os
import sys
from urllib.parse import urlencode, quote_plus, unquote_plus


from dotenv import dotenv_values
import requests

config = {
    **dotenv_values(".env"),  # load shared development variables
    **os.environ,  # override loaded values with environment variables
}
config["ACCEPT"] = "application/json"
config["PATH"] = "/2.0.0/search"


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
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def result(documents):
    """
    Print output/summary of search results.
    """
    print(f"Search Results: {len(documents)}")
    for doc in documents:
        # TODO strip <h> highlight tags from title
        print(f"Title: {doc['Title'][0]}")
        print(f"Authors: {', '.join(doc['Author'])}")
        print(f"Publication Date: {doc['PublicationDate'][0]}")
        print(f"ISBNs: {', '.join(doc['ISBN'])}")
        print(f"Type: {doc['ContentType'][0]}")
        print(
            f"Summon Link: https://{config['ACCESS_ID']}.summon.serialssolutions.com/search?bookMark={doc['BookMark'][0]}"
        )
        print("")


if __name__ == "__main__":
    params = {
        "s.q": f'"{sys.argv[1]}"',
        "s.fvf": ["SourceType,Library Catalog,f"],
    }
    print(result(search(params).get("documents", [])))
