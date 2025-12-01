from pathlib import Path

import click
from pymarc import Field, MARCReader, Record


@click.command()
@click.help_option("-h", "--help")
@click.argument(
    "file",
    metavar="<input.mrc>",
    type=click.Path(exists=True, readable=True),
)
def print_duplicates(file: Path):
    """Print records with duplicate 001s from a MARC file."""
    count: int = 0
    records: dict[str, list[Record]] = {}
    reader = MARCReader(open(file, "rb"))
    click.echo(
        f"Scanning {file} for duplicates, this takes time depending on the file size."
    )

    for record in reader:
        if record:
            id_field: list[Field] = record.get_fields("001")
            if id_field and len(id_field) == 1:
                record_id: str | None = id_field[0].value()
                if record_id:
                    records.setdefault(record_id, []).append(record)

    for record_id, recs in records.items():
        if len(recs) > 1:
            count += 1
            for rec in recs:
                link: str = ""
                sysctl_field: Field | None = rec.get("999")
                if sysctl_field:
                    biblionumber: str | None = sysctl_field.get("c")
                    if biblionumber:
                        link: str = f"https://library-staff.cca.edu/cgi-bin/koha/catalogue/detail.pl?biblionumber={biblionumber}"
                title: str = rec.title if rec.title else "[no title]"
                click.echo(f"{title} {link}")

    click.echo(f"{count} duplicates out of {len(records)} unique 001s")


if __name__ == "__main__":
    print_duplicates()
