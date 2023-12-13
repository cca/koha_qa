# Koha Records QA

Various bibliographic metadata tools.

## Setup

To use summon.py, obtain a Summon API key from the Ex Libris Developer Network, see [their documentation](https://knowledge.exlibrisgroup.com/Summon/Product_Documentation/Configuring_The_Summon_Service/Configurations_Outside_of_the_Summon_Administration_Console/Summon%3A_Using_the_Summon_API).

```sh
pipenv install
cp example.env .env
vim .env # edit in API key
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

## summon.py

Check if a MARC record is in CCA's Summon instance.

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
> pipenv run python summon.py --missing missing.csv path/to/records.mrc

Records: 174
Found: 165
ISBN Matches: 155
```

This is a pretty unsophisticated check right now. A record with any search result is considered in Summon, and the ISBN test is only the first ISBN against all Summon ISBNs (not all against all).

## LICENSE

[ECL Version 2.0](https://opensource.org/licenses/ECL-2.0)

Code from Summon API Toolkit may come with a different license but none was stated in their GitHub repo.
