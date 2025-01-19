"""
Add our proxy server prefix to the 856$u subfield in Comics Plus MARC records.
Also, print a warning for "c" corrected or "d" deleted records which we will have
to test for in the future.
"""

import argparse
from datetime import date

from pymarc import (
    Indicators,
    MARCReader,
    MARCWriter,
    Record,
    Field,
    Subfield,
    Indicators,
)


def is_update_or_delete(record):
    """Print message if we find a corrected or deleted record"""
    # https://www.loc.gov/marc/bibliographic/bdleader.html
    status = record.leader[5]
    # ! Comics Plus doesn't seem to use "c" for corrected records
    if status in ["c", "d"]:
        print(
            f"Warning {'corrected' if status == 'c' else 'deleted'} record: {record.title}"
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


def fix_538(record: Record):
    # Remove junk 538s
    for field in record.get_fields("538"):
        a = field.get("a")
        if type(a) == str and "Mode of access: World Wide Web" in a:
            record.remove_field(field)
        if type(a) == str and "Requires a valid library card and registration" in a:
            record.remove_field(field)
        if type(a) == str and "System requirements:" in a:
            record.remove_field(field)

    # add a better-worded 538 but don't duplicate it
    has_our_538 = False
    msg = 'Use the "Sign Up" link to create a LibraryPass account. You must have an account to read the ebook.'
    for field in record.get_fields("538"):
        a = field.get("a")
        if type(a) == str and msg in a:
            has_our_538 = True
    if not has_our_538:
        record.add_ordered_field(
            Field(
                tag="538",
                subfields=[
                    Subfield(
                        code="a",
                        value='Use the "Sign Up" link to create a LibraryPass account. You must have an account to read the ebook.',
                    )
                ],
            )
        )


def rda_ebook(record: Record):
    """Remove 245$h GMD and add RDA 336/337/338 fields"""
    for field in record.get_fields("245"):
        field.delete_subfield("h")

    # 33x fields
    if not record.get("336"):
        record.add_ordered_field(
            Field(
                tag="336",
                subfields=[
                    Subfield(code="a", value="text"),
                    Subfield(code="b", value="txt"),
                    Subfield(code="2", value="rdacontent"),
                ],
            )
        )
        # graphic novels have text _and_ image content
        record.add_ordered_field(
            Field(
                tag="336",
                subfields=[
                    Subfield(code="a", value="still image"),
                    Subfield(code="b", value="sti"),
                    Subfield(code="2", value="rdacontent"),
                ],
            )
        )
    if not record.get("337"):
        record.add_ordered_field(
            Field(
                tag="337",
                subfields=[
                    Subfield(code="a", value="computer"),
                    Subfield(code="b", value="c"),
                    Subfield(code="2", value="rdamedia"),
                ],
            )
        )
    if not record.get("338"):
        record.add_ordered_field(
            Field(
                tag="338",
                subfields=[
                    Subfield(code="a", value="online resource"),
                    Subfield(code="b", value="cr"),
                    Subfield(code="2", value="rdacarrier"),
                ],
            )
        )


def lcgft(record: Record):
    """Add LC Genre/Form Term for Graphic novels"""
    has_gn = False
    for field in record.get_fields("655"):
        a = field.get("a")
        if type(a) == str and "Graphic novels" in a:
            has_gn = True
    if not has_gn:
        record.add_ordered_field(
            Field(
                tag="655",
                indicators=Indicators(" ", "7"),
                subfields=[
                    Subfield(code="a", value="Graphic novels"),
                    Subfield(code="2", value="lcgft"),
                ],
            )
        )


def remove_librarypass(record: Record):
    """Remove references to LibraryPass in 245, 710"""
    for field in record.get_fields("245"):
        c = field.get("c")
        if type(c) == str and ("Library Pass" in c or "LibraryPass" in c):
            field.delete_subfield("c")
    for field in record.get_fields("710"):
        a = field.get("a")
        if type(a) == str and ("Library Pass" in a or "LibraryPass" in a):
            record.remove_field(field)


def add_cca(record: Record):
    field = record.get("040")
    if field:
        if "CC9" not in field.get_subfields("a", "b", "c", "d"):
            field.add_subfield(code="d", value="CC9")
    else:
        # this should probably never happen but...
        record.add_ordered_field(
            Field(
                tag="040",
                subfields=[
                    Subfield(code="a", value="CC9"),
                    Subfield(code="e", value="rda"),
                ],
            )
        )


def koha_ebook(record: Record):
    """Koha stores local information in 942, $c is default item type"""
    field = record.get("942")
    if field:
        if "EBOOK" not in field.get_subfields("c"):
            field.add_subfield(code="c", value="EBOOK")
    else:
        record.add_field(
            Field(tag="942", subfields=[Subfield(code="c", value="EBOOK")])
        )


def process_record(record: Record) -> Record:
    """Process MARC record"""
    is_update_or_delete(record)
    for field in record.get_fields("856"):
        proxy_856(field)
    fix_538(record)
    rda_ebook(record)
    lcgft(record)
    remove_librarypass(record)
    add_cca(record)
    return record


def process_marc(file, output):
    """Parse MARC file and search for items."""
    reader = MARCReader(open(file, "rb"))
    writer = MARCWriter(open(output, "wb"))
    for record in reader:
        if record:
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
