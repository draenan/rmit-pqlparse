#!/usr/bin/env python
"""Processes a file containing PQL output and produces either JSON
with the the original objects merged on 'certname', or CSV output.
"""

import argparse
import errno
import json
import sys

__author__ = "Adrian Waters <adrian.waters@rmit.edu.au>"

def load_json_data(data_file):
    """Loads the JSON data from the input file.

    Args:
        data_file: Reference to a file object containing the data to
        parse.
    Raises:
        IOError: There was a problem opening the file.
        ValueError: There was a problem loading the JSON from the file.
    Returns:
        Dictionary of the JSON data in the file.
    """

    try:
        data = json.load(data_file)
    except (IOError, ValueError) as err:
        print err
        raise
    return data


def parse_json_data(data):
    """Creates a new list of JSON objects by merging individual PQL output
    JSON object on the 'certname' attribute.

    Args:
        data: List of dictionary representations of PQL JSON objects.
    Returns:
        New list of dictionary representations of JSON objects merged on
        'certname' attribute.
    """

    """
    Note that there is a logic bug in this code that would manifest if the
    output of puppet-query was proper unordered JSON.  However puppet-query
    appears to be outputting JSON grouped by "certname", so the bug doesn't
    trigger.  To guard against this changing the query should have an
    "order by certname" clause.
    """

    new_objects = []
    new_object = {}
    for obj in data:
        try:
            if obj['certname'] != new_object['certname']:
                new_objects.append(new_object)
                new_object = {}
                new_object['certname'] = obj['certname']
        except KeyError:
            new_object['certname'] = obj['certname']
        new_object[obj['name']] = obj['value']
    new_objects.append(new_object)
    return new_objects


def output_as_json(data, json_type=None):
    """Takes a list of JSON objects and prints them out to stdin.

    The format can be either minified JSON, or the default "pretty print" JSON.

    Args:
        data: A list of dictionaries representing JSON objects.
        json_type: Optional string, outputs minified JSON if set to "minjson",
        pretty print JSON is produced.
    Returns:
        Nothing.  JSON content is output to stdin.
    """

    if json_type == 'minjson':
        print json.dumps(data, separators=(',', ':'))
    else:
        print json.dumps(data, indent=4)


def output_as_csv(data, fact_mappings=None):
    """Takes a list of JSON objects and converts them to CSV output.

    CSV columns can be defined via an optional String of fact name/column
    pairs.  If the string is supplied the output will only contain the facts in
    the string, otherwise all facts in the JSON data will be used (preceeded by
    'certname' in the first column.)  If the namepair string is supplied and
    a column name is missing from the pair the fact name will be used as the
    column name.

    For example: "certname=hostname,operatingsystem=Operating System",
    "certname=hostname,operatingsystem"

    Args:
        data: A list of dictionaries representing JSON objects.
        fact_mappings: Optional String of comma seperated fact name to
        column name pairs (eg "certname=hostname,operatingsystem=Operating System").
    Returns:
        Nothing.  CSV content is output to stdin.
    """

    column_names = []
    fact_names = set()
    fact_column_map = {}

    if fact_mappings:
        fact_maps = fact_mappings.split(',')
        for fact_map in fact_maps:
            try:
                fact_name, column_name = fact_map.split('=')
            except ValueError:
                fact_name = fact_map
                column_name = fact_name
            column_names.append(column_name)
            fact_column_map[column_name] = fact_name
    else:
        for obj in data:
            for key in obj:
                if key != 'certname':
                    fact_names.add(key)

        fact_names = sorted(list(fact_names))
        fact_names.insert(0, u'certname')
        column_names = fact_names

    __generate_csv_output(data, column_names, fact_column_map)


def __generate_csv_output(data, column_names, fact_column_map=None):
    """Takes JSON data, a list of column names, and an optional
    fact name to column name mapping and uses them to produce
    CSV output.

    Existence of this private function is primarily to stop pylint
    from complaining about too many branches in output_as_csv().

    Args:
        data: A list of dictionaries representing JSON objects.
        column_names: A sorted list of CSV column names.
        fact_column_map: An optional dictionary mapping fact names to
        column names.
    Returns:
        Nothing.  The output is sent direct to stdout via 'print'.
    """
    header = ','.join(column_names)
    print header

    for obj in data:
        values = []
        for column_name in column_names:
            try:
                if fact_column_map:
                    value = obj[fact_column_map[column_name]]
                else:
                    value = obj[column_name]
            except KeyError:
                value = u'Undefined'
            values.append(str(value).replace(',', '_'))
        line = ','.join(values)
        print line


def _main():
    """Main function, for use when pqlparse.py is run as a script.

    Args:
        Whatever is in sys.argv as implemented by argparse.
    Returns:
        Return code "1" on error, "130" on interrupt.
    """

    parser = argparse.ArgumentParser(description='''Processes a file containing
                                     PQL output and produces either JSON with
                                     the original objects merged on 'certname',
                                     or CSV output.''')
    group = parser.add_mutually_exclusive_group()

    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
                        default=sys.stdin,
                        help='''Filename of PQL output to process.''')
    group.add_argument('-o', '--outformat', choices=['json', 'minjson', 'csv'],
                       help='''Choose the output format: JSON (the default), minified
                       JSON, or CSV.  Use of this option for CSV will produce output
                       with 'certname' in the first field of the line, then
                       remaining facts from JSON file in ascending sort order.''')
    group.add_argument('-H', '--headers',
                       help='''String of comma-separated values for use as CSV headers
                       with optional factname-to-header mapping (factname=header).
                       Implies that the output format will be CSV.''')

    args = parser.parse_args()

    try:
        query_results = load_json_data(args.infile)
    except (IOError, ValueError):
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)

    new_json = parse_json_data(query_results)

    try:
        if args.outformat == 'csv' or args.headers is not None:
            output_as_csv(new_json, args.headers)
        else:
            output_as_json(new_json, args.outformat)
    except IOError as err:
        if err.errno == errno.EPIPE:
            pass


if __name__ == "__main__":
    _main()
