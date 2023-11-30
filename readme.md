# Summon Record Check

Check if a MARC record is in CCA's Summon instance.

## Setup

Obtain a Summon API key from the Ex Libris Developer Network, see [their documentation](https://knowledge.exlibrisgroup.com/Summon/Product_Documentation/Configuring_The_Summon_Service/Configurations_Outside_of_the_Summon_Administration_Console/Summon%3A_Using_the_Summon_API).

```sh
pipenv install
cp example.env .env
vim .env # edit in API key
```

## Usage

```sh
# search for single title
pipenv run python app.py "the color purple"
# iterate over file of MARC records
pipenv run python app.py path/to/records.mrc
```

## LICENSE

[ECL Version 2.0](https://opensource.org/licenses/ECL-2.0)

Code from Summon API Toolkit may come with a different license but none was stated in their GitHub repo.
