# fix_rrd_missing_ds
[RRD File] Fix missing DS records

Fixes missing DS records of RRD files by comparing metrics DS count with DS count of RRD file.

Using python-rrdtool which comes with CheckMK to analyze and add missing DS records.

Usage: 

        fix_rrd_missing_ds.py [-h] [-v] [--force] [--debug] [--rrdfile RRDFILE]

Optional arguments:

        -h, --help         show this help message and exit
        -v                 Enable verbose output
        --force            Apply changes, .bak files will be created but still handle with care!
        --debug            Enable debugging level in logging
        --rrdfile RRDFILE  Single RRD file to process

A logfile will be created at 
        
        $OMD_ROOT/var/log/fix_rrd_missing_ds_records.log

Changelog

        1.0 Initial release
        1.1 Added some counters

Disclaimer: This tool comes without warranty, use at your own risk.
