from io import TextIOWrapper
from pathlib import Path

import click
from pymarc import MARCReader, MARCWriter


def get_writer(n: int):
    fh = open(f"records-{n + 1}.mrc", "wb")
    writer = MARCWriter(fh)
    return writer


@click.command()
@click.help_option("-h", "--help")
@click.argument("N", type=click.INT)
@click.argument("file", type=click.File("rb"), metavar="file.mrc")
def main(n: int, file: TextIOWrapper):
    """break MARC file into smaller ones of N or less records"""
    count = 0
    files = 0
    reader = MARCReader(file)  # type: ignore
    writer = get_writer(files)
    for record in reader:
        if record:
            if count < n:
                writer.write(record)
                count += 1
            else:
                # close writer (also closes fh) & write to next file
                writer.close()
                click.echo(f"Wrote {count} records to records-{files + 1}.mrc")
                files += 1
                writer = get_writer(files)
                writer.write(record)
                count = 1
    # final file if it has < n records
    if count != n:
        click.echo(f"Wrote {count} records to records-{files + 1}.mrc")


if __name__ == "__main__":
    main()
