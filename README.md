# pqlparse.py - Python 2 parser for Puppet Query Language JSON output

```
usage: pqlparse.py [-h] [-o {json,minjson,csv} | -H HEADERS] file

Processes a file containing PQL JSON output and produces either JSON with the
original objects merged on 'certname', or CSV output.

positional arguments:
  file                  File of PQL JSON output to process

optional arguments:
  -h, --help            show this help message and exit
  -o {json,minjson,csv}, --outformat {json,minjson,csv}
                        Choose the output format: JSON (the default), minified
                        JSON, or CSV. Use of this option for CSV will produce
                        output with 'certname' in the first field of the line,
                        then remaining facts from JSON file in ascending sort
                        order.
  -H HEADERS, --headers HEADERS
                        String of comma-separated values for use as CSV
                        headers with optional factname-to-header mapping
                        (factname=header). Implies that the output format will
                        be CSV.
```

`pqlparse.py` takes JSON output from `puppet query` and converts it into
a usable form, with the intent being to replicate MCollective's `inventory`
functionality and report formatting.  That is, it will take an array of JSON
objects derived via PQL-based queries to PuppetDB of the form:

```
[
  {
    "certname": "foo.example.com",
	"name": "operatingsystem",
	"value": "RedHat"
  },
  {
    "certname": "foo.example.com",
	"name": "operatingsystemmajrelease",
	"value": "7"
  }
]
```
and convert it  to:

```
[
  {
    "certname": "foo.example.com",
	"operatingsystem": "RedHat",
	"operatingsystemmajrelease": "7"
  }
]
```
These JSON objects are then sent to `stdout` as either "prettified" JSON,
minified JSON, or CSV with a header based on fact names and with `certname` as
the first value.  For example, the above output could be represented in
minified JSON by passing the `-o minjson` argument; as CSV by passing the `-o
csv` argument; or CSV with defined headers via `-H
"certname=Hostname,operatingsystem=Operating System,operatingsystemmajrelease=OS Release"`.

Note when using the `-H` argument it isn't a requirement that a column name to
fact name mapping be used, nor is it a requirement that all facts by used.  For
example, `-H "certname=Hostname,operatingsystem"` when used with the above
converted JSON example would produce CSV output:

```
Hostname,operatingsystem
foo.example.com,RedHat
```

## Helper Script

A helper script, `mail_report.sh` has been included to assist with generating
and emailing reports based on report definitions in a config file consisting of
various shell variables which are then sourced by the script.  Check the
inlcuded `sample.report` for further information.

```
Usage: mail_report.sh [-d] [-v] [-n] file

Required parameter:
    file            File containing report definition

Optional parameters:
    -h              Show this help message and exit
    -d              Debug mode (noop, implies '-n')
    -v              Be verbose
    -n              Do not email report

```

