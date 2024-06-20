import csv
from datetime import date
import io
import logging
from pathlib import Path
import os
import signal
import sys

from dotenv import dotenv_values
import httpx

config: dict = {
    **dotenv_values(".env"),  # load shared development variables
    **os.environ,  # override loaded values with environment variables
}
today = date.today().isoformat()

# log to both file & console in CSV-like format, we have to get pretty hacky to
# do CSV formatting for logging a list (not single message value)
logging.basicConfig(
    datefmt="%Y-%m-%d %H:%M:%S",
    format='"%(asctime)s","%(levelname)s",%(message)s',
    handlers=[
        logging.FileHandler(
            Path("data") / config.get("LINKCHECK_LOG_FILE", f"{today}-linkcheck.csv")
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger()

# global HTTP statuses, looks like {200: 1, 404: 2, exception: 3}
statuses: dict[int | str, int] = {"exception": 0}


def quote(list):
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)
    writer.writerow(list)
    return output.getvalue().strip()


def main() -> None:
    report = httpx.get(config["LINKCHECK_REPORT"])
    for bib in report.json():
        # bibs are arrays like [urls string, title, biblionumber]
        urls, title, id = bib
        # urls are separated by " | "
        urls = urls.split(" | ")
        for url in urls:
            try:
                r = httpx.get(url, follow_redirects=True)
                status = r.status_code
                if not statuses.get(status):
                    statuses[status] = 0
                statuses[status] += 1
                # distinguish between severity of 5XX & 4XX HTTP errors
                if status >= 500:
                    logger.error(
                        quote(
                            [
                                title,
                                config["LINKCHECK_OPAC_URL"].format(id=id),
                                status,
                                url,
                            ]
                        )
                    )
                elif status >= 400:
                    logger.warning(
                        quote(
                            [
                                title,
                                config["LINKCHECK_OPAC_URL"].format(id=id),
                                status,
                                url,
                            ]
                        )
                    )
            except:
                logger.error(
                    quote(
                        [
                            title,
                            config["LINKCHECK_OPAC_URL"].format(id=id),
                            "HTTP Exception",
                            url,
                        ]
                    )
                )
                statuses["exception"] += 1


def summarize() -> None:
    print("Link check summary:")
    print(statuses)


def signal_handler(sig, frame) -> None:
    print("Caught SIGINT, printing summary")
    summarize()
    sys.exit(1)


if __name__ == "__main__":
    # TODO this doesn't seem to work with httpx it cancels the current request
    # TODO but the script keeps running
    signal.signal(signal.SIGINT, signal_handler)
    main()
