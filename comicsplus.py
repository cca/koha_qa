"""
Add our proxy server prefix to the 856$u subfield in Comics Plus MARC records.
Also, print a warning for "c" corrected or "d" deleted records which we will have
to test for in the future.
"""

import argparse
from datetime import date

from pymarc import MARCReader, MARCWriter, Record


def is_update_or_delete(record):
    """Print message if we find a corrected or deleted record"""
    # https://www.loc.gov/marc/bibliographic/bdleader.html
    status = record.leader[5]
    # ! Comics Plus doesn't seem to use "c" for corrected records
    if status in ["c", "d"]:
        print(
            f"Warning: {'corrected' if status == 'c' else 'deleted'} record: {record.title}"
        )


def proxy(url):
    """Add proxy prefix to URL"""
    return f"https://login.proxy.cca.edu/login?url={url}"


def proxy_856(field):
    """Add proxy prefix to 856$u subfield"""
    # ! this approach won't work if there are multiple u or z subfields
    for url in field.get_subfields("u"):
        if "californiacollegeoftheartsca.librarypass.com" in url:
            field.delete_subfield("u")
            field.add_subfield("u", proxy(url))
    for public_note in field.get_subfields("z"):
        if "Instantly available" in public_note:
            field.delete_subfield("z")
            field.add_subfield(
                "z", "Read ebook in Comics Plus (account creation required)"
            )


def process_record(record) -> Record:
    """Process MARC record"""
    is_update_or_delete(record)
    for field in record.get_fields("856"):
        proxy_856(field)
    return record


def process_marc(file, output):
    """Parse MARC file and search for items."""
    reader = MARCReader(open(file, "rb"))
    writer = MARCWriter(open(output, "wb"))
    for record in reader:
        new_record = process_record(record)
        writer.write(new_record)


if __name__ == "__main__":
    default_output = f"{date.today().isoformat()}-comicsplus.mrc"
    parser = argparse.ArgumentParser(description="Process Comics Plus MARC records")
    parser.add_argument("input", metavar="<file.mrc>", help="MARC file to process")
    parser.add_argument(
        "output",
        metavar="<output.mrc>",
        default=default_output,
        help=f"Output filename, defaults to {default_output}",
        nargs="?",
    )
    args = parser.parse_args()
    process_marc(args.input, args.output)
