# Koha Records QA

Various bibliographic metadata tools.

## Setup

To use summon.py, obtain a Summon API key from the Ex Libris Developer Network, see [their documentation](https://knowledge.exlibrisgroup.com/Summon/Product_Documentation/Configuring_The_Summon_Service/Configurations_Outside_of_the_Summon_Administration_Console/Summon%3A_Using_the_Summon_API). To use summon-update.py, add our Summon SFTP credentials to the .env file.

This project is an experiment in using [uv](https://github.com/astral-sh/uv) for python package management. Prefix python commands with `uv run` to use the project's virtual environment.

```sh
uv sync
cp example.env .env
vim .env # edit in secret values
```

## break.py

Split MARC files into smaller subsets named like `records-1.mrc`, `records-2.mrc`, etc. This is the same as MARCEdit's MARCSplit feature if you would prefer not to use the command line. Koha can only process so many records at once without failing so we tend to batch record imports at 500 or 1000 records at a time.

```sh
Usage: break.py [OPTIONS] N file.mrc

  break MARC file into smaller ones of N or less records

Options:
  -h, --help  Show this message and exit.
```

## comicsplus.py

Add our proxy server prefix to Comics Plus MARC records and warn if there are any corrected or deleted records. See [our wiki page](https://sites.google.com/cca.edu/librarieswiki/home/cataloging/ebook-import/comicsplus) on Comics Plus for more information and why we cannot accomplish this with Koha's MARC modification templates.

```sh
usage: comicsplus.py [-h] <file.mrc> [<output.mrc>]

Process Comics Plus MARC records

positional arguments:
  <file.mrc>    MARC file to process
  <output.mrc>  Output filename, defaults to YYYY-MM-DD-comicsplus.mrc

options:
  -h, --help    show this help message and exit
```

## linkcheck.py

Check URLs in Koha 856$u fields. See [the readme](./linkcheck/readme.md) for details.

## summon.py

Check if MARC record(s) are in CCA's Summon index.

```sh
# search for single title with detailed search results output
> pipenv run python summon.py --debug "the color purple"
https://cca.summon.serialssolutions.com/search?s.q=%22the+color+purple%22&s.fvf=SourceType%2CLibrary+Catalog%2Cf
Search Results: 10
Title: The color purple
Authors: Walker, Alice
Publication Date: 1983.
ISBNs: 0671668781, 9780671668785, 0156031825, 9780156031820, 0671617028, 9780671617028, 9780151191543, 0151191549
Type: Book
Summon Link: https://cca.summon.serialssolutions.com/search?bookMark=...
# more search results printed...

# iterate over MARC records with summary output and CSV of missing records
> pipenv run python summon.py --missing missing.csv file.mrc

Total Records:      50
Had Search Results: 50
Had ISBN:           46
ISBN Matches:       45
```

A record is considered "missing" if there is no ISBN match in Summon, records without ISBNs are not considered missing. The Summon search is a title search, so records with short, generic titles like "Art Now" can be considered "missing" because the record with the matching ISBN isn't in the first page of 10 search results returned.

## summon-update.py

Update our Summon index with a file of MARC records. Can delete or update records. A "full" update requires contacting support but this script can upload the file. Export records from Koha staff side > Cataloging > [Export data](https://library-staff.cca.edu/cgi-bin/koha/tools/export.pl).

```sh
Usage: summon-update.py [OPTIONS] FILE_PATH

  Puts a file to the Summon SFTP server.

Options:
  -h, --help                      Show this message and exit.
  -t, --type [updates|deletes|full]
                                  type of update
  -d, --debug                     enable SFTP debug logging
```

## LICENSE

[ECL Version 2.0](https://opensource.org/licenses/ECL-2.0)

Code from Summon API Toolkit may come with a different license but none was stated in their GitHub repo.
