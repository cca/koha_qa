# Check links in MARC records

Takes a public Koha report and checks each URL (`856$u`) to see if they resolve successfully. Logs output to console and a CSV file.

## Environment Variables

The script uses the same .env file as the root project or it can take environment variables.

- `LINKCHECK_LIMIT` number of links to check (leave undefined for all of them)
- `LINKCHECK_REPORT` URL to a Koha report that returns item URLs (see [report.sql](./report.sql)). Report must be Public.
- `LINKCHECK_OPAC_URL` catalog link for individual records, should include `biblionumber={id}` in it (id is interpolated)
- `LINKCHECK_LOGFILE` path to logged CSV, defaults to the data dir named "YYYY-MM-DD-linkcheck.csv" with today's date

## Notes

The app prints URLs with non-200 HTTP response statuses. It also catches HTTP exceptions within httpx, which can occur when a domain is unavailable.

Some websites have poor server hygiene and send successful HTTP responses with non-200 error codes. Not much we can do about that.
