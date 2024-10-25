# puts MARC file to our Summon SFTP server
# https://knowledge.exlibrisgroup.com/Summon/Product_Documentation/Configuring_The_Summon_Service/Working_with_Local_Collections_in_the_Summon_Service/Getting_Local_Collections_Loaded_into_the_Summon_Index/Summon%3A_Exporting_Catalog_Holdings_-_Uploading_to_Summon
from datetime import datetime
import logging
import os
from typing import Literal

import click
from dotenv import dotenv_values
from pymarc import MARCReader, Record
import pysftp

config = {
    **dotenv_values(".env"),  # load shared development variables
    **os.environ,  # override loaded values with environment variables
}
# log to data/log.txt and stdout
logformat = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(
    filename=config.get("SUMMON_LOG_FILE", "data/log.txt"),
    level=logging.INFO,
    format=logformat,
)
# also to stdout
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter(logformat)
console.setFormatter(formatter)
logging.getLogger("summon_update").addHandler(console)
logger: logging.Logger = logging.getLogger("summon_update")

# fix pysftp bug "AttributeError: 'Connection' object has no attribute '_sftp_live'"
cnopts = pysftp.CnOpts()
cnopts.hostkeys = None


def rename(filetype: str) -> str:
    """rename MARC file using Summon CDI conventions

    Args:
        filetype (str): type of update (deletes, updates, full)

    Returns:
        str: filename formatted for Summon SFTP server
    """
    return f"cca-catalog-{filetype}-{datetime.now().strftime('%F-%H-%M-%S')}.mrc"


@click.command()
@click.argument("file_path")
@click.help_option("--help", "-h")
@click.option(
    "-t",
    "--type",
    "filetype",
    help="type of update",
    required=True,
    type=click.Choice(["updates", "deletes", "full"]),
)
@click.option(
    "-d", "--debug", is_flag=True, help="enable SFTP debug logging", flag_value=1
)
def put_file(
    file_path: str,
    filetype: Literal["updates", "deletes", "full"],
    debug: Literal[1, None] = None,
) -> None:
    """
    Puts a file to the Summon SFTP server.
    """
    # we need to know the number of records for Summon admin
    with open(file_path, "rb") as fh:
        reader = MARCReader(fh)
        # count=1 for non-MARC files if we don't include the isinstance check
        count: int = sum(1 for record in reader if isinstance(record, Record))
        if count and count != 0:
            logger.info(f"Number of records in {file_path}: {count}")
        else:
            logger.error(
                f"No records found in {file_path}. Are you sure it's a MARC file?"
            )
            exit()

    remote_path: str = f"{filetype}/{rename(filetype)}"
    with pysftp.Connection(
        cnopts=cnopts,
        host=config["SUMMON_SFTP_HOST"],
        log=debug,  # type: ignore
        port=int(config.get("SUMMON_SFTP_PORT", 22)),
        private_key=config["SUMMON_SFTP_KEY"],
        username=config["SUMMON_SFTP_USER"],
    ) as sftp:
        sftp.put(file_path, remote_path)
        logger.info(f"File {file_path} put to {remote_path}")


if __name__ == "__main__":
    put_file()
