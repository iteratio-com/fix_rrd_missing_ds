#!/usr/bin/env python3

import rrdtool
import pathlib
import os
import re
import shutil
import argparse
import logging

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(funcName)s - %(levelname)s - %(message)s',
    filename=f"{os.environ['OMD_ROOT']}/var/log/fix_rrd_missing_ds_records.log",
)

# Folders
BASEDIR = os.environ.get('OMD_ROOT')
RRDDIR = BASEDIR + "/var/check_mk/rrd/"

def parse_arguments(argv=None):
    defaults = (('rrdfile', None, 'Single RRD file to process'),)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--force", action="store_true", help="Apply changes, .bak files will be created but still handle with care!")
    parser.add_argument("--debug", action="store_true", help="Enable debugging level in logging")
    opt_with_help = (t for t in defaults if len(t) == 3)
    for key, default, help_string in opt_with_help:
        if default is not None:
            help_string += ", Default: %s" % default
        parser.add_argument("--%s" % key, default=default, help=help_string)

    return parser.parse_args(argv)


def main(argv=None):
    rrdfiles = []
    single = False
    args = parse_arguments(argv)
    logger = logging.getLogger()

    if args.v:
        s = logging.StreamHandler()
        logger.addHandler(s)

    logger.info("-"*80)

    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Logger is set to DEBUG!")

    if args.force:
        force = True
        logger.info("FORCE MODE SET - changes will be applied")
    else:
        force = False

    if args.rrdfile:
        single_rrdfile = str(args.rrdfile)
        single = True

    if single:
        rrdfiles.append(single_rrdfile)
        logger.info(f"Processing single file")
    else:
        rrdfiles = pathlib.Path(RRDDIR).glob('**/*.rrd')

    for rrdfile in rrdfiles:
        dslist = []
        rrdfile = str(rrdfile)
        rrdhost = rrdfile.split("/")[7]
        infofile = re.sub("rrd$", "info", rrdfile)

        if not os.path.exists(infofile):
            logger.error(f"{rrdhost}/{os.path.basename(infofile)} is missing, skipping")
            continue

        with open(infofile) as info:
            for line in info:
                if line.startswith('METRICS'):
                    metrics = line.split(" ")[1]
                    infods = len(metrics.split(";"))

        if single:
            logger.info(f"Checking RRD file {rrdfile}")
        else:
            logger.debug(f"checking RRD file {rrdfile}")

        rrdfilecontent = rrdtool.info(rrdfile)
        for k, v, in rrdfilecontent.items():
            if k.startswith('ds['):
                ds = int(k.split(".")[0].replace("ds[","").replace("]",""))
                if ds not in dslist:
                    dslist.append(ds)

        if len(dslist) != infods:
            missingds = []
            logger.error(
                f"{rrdhost}/{os.path.basename(rrdfile)}: {len(dslist)} metrics != {os.path.basename(infofile)}: {infods} metrics"
            )

            if force == True:
                backupfile = re.sub("rrd$", "bak", rrdfile)
                logger.info(f"Backing up for {rrdhost} {os.path.basename(rrdfile)} to {os.path.basename(backupfile)}")
                shutil.copyfile(rrdfile,backupfile)

            for ds in range(dslist[0], dslist[-1] + 1):
                if ds not in dslist:
                    missingds.append(ds)
                    if force == True:
                        rrdtool.tune(rrdfile, f'DS:{ds}:GAUGE:8460:0:U')
                    logger.info(f"rrdtool tune {rrdfile} DS:{ds}:GAUGE:8460:0:U")

            # if we do not miss inbetween but DS at the end, the sequence would be consistent
            # in that case we need to set a virtual limit manually and re-check
            if len(missingds) == 0:
                dslist.append(infods + 1)
                for ds in range(dslist[0], dslist[-1] + 1):
                    if ds not in dslist:
                        missingds.append(ds)
                        if force == True:
                            rrdtool.tune(rrdfile, f'DS:{ds}:GAUGE:8460:0:U')
                        logger.info(f"rrdtool tune {rrdfile} DS:{ds}:GAUGE:8460:0:U")
        else:
            logger.debug(f"RRD file {rrdhost}/{os.path.basename(rrdfile)} has same count of DS in info file, no reparation needed")


main()
