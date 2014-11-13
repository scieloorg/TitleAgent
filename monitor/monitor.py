# coding: utf-8
'''
This utilitary intends to monitor changes made in the SciELO Title Manager
catalog.
'''
import argparse
import os
import logging
import time
import hashlib
import random
import json
from io import BytesIO

from isis2json import isis2json
from xylose.scielodocument import Journal

from articlemetarpcclient import ArticleMetaRPCClient

THROTTLE_TIME = 60*10 # 10 minutes

class ItemsChecksum(object):

    def __init__(self):
        self.items = {}

    def is_checksum_equal(self, item, raw_data):
        current_checksum = hashlib.md5(raw_data).hexdigest()

        checksum = self.items.get(item, None)

        if not checksum or checksum != current_checksum:
            self.items[item] = current_checksum
            return False

        return True

CHECKSUMS = ItemsChecksum()


def _config_logging(logging_level='INFO', logging_file=None):

    allowed_levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    logging_config = {
        'level': allowed_levels.get(logging_level, 'INFO'),
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    }

    if logging_file:
        logging_config['filename'] = logging_file

    logging.basicConfig(**logging_config)


class CISIS(object):
    """
    A Small CISIS interface to run MX commands
    """

    def __init__(self, isispath):
        if not os.path.exists(isispath) or not os.path.exists("%s/mx" % isispath):
            logging.error('ISIS path invalid or withthout [mx]: %s' % isispath)
            raise ValueError

        self.isispath = isispath
        self.mxpath = '%s/mx' % isispath

    @property
    def version(self):
        command = '%s what' % self.mxpat
        return os.popen(command).read()

    def iso(self, database):
        filename = '/tmp/%s.iso' % hashlib.md5(str(random.random())).hexdigest()
        command = "{0} {1} {2}".format(
            self.mxpath,
            database,
            'iso=%s -all now' % filename
        )

        os.popen(command)

        return open(filename, 'rb')

    def isis2json(self, database):
        iso_database = self.iso(database)

        bytesdata = BytesIO()

        isis2json.writeJsonArray(
            isis2json.iterIsoRecords, # iter records using iso mode.
            iso_database, # database filelike
            bytesdata, # output stream
            2**31, # number of records to load in memory
            0, # number of documents to skip
            0, # id tag
            False, # gen uuid field
            False, # MongoDB output?
            False, # generate an "_id" from the MFN of each record
            3, # ISIS-JSON type, sets field structure: 1=string, 2=alist, 3=dict (default=1)
            'v', # prefix example v100
            '' # Include a constant tag:value in every record (ex. -k type:AS)
        )

        data = json.loads(bytesdata.getvalue())

        bytesdata.close()

        return data

def inspect_file(filename):
    """
        The monitored file must exists and must be a mst file.
    """

    if not os.path.exists(filename):
        logging.error('Monitored file does not exists: %s' % filename)
        return False

    if filename[-3:] != 'mst':
        logging.error('Monitored file is not a mst file: %s' % filename)
        return False

    return True

def dispatcher(documents, collection):
    logging.info('There are %d files eligible to send' % len(documents))

    amrpc = ArticleMetaRPCClient()

    for document in documents:
        document['v992'] = [{'_': collection}]
        xdoc = Journal(document)
        if not CHECKSUMS.is_checksum_equal(
            xdoc.collection_acronym+xdoc.scielo_issn,
            str(len(json.dumps(document)))
        ):
            logging.debug('Journal will be updated: %s' % xdoc.title)
            amrpc.add_journal(document)

def main(monitored_file, cisis_path, collection, throttle=THROTTLE_TIME):
    logging.info('Starting Title Manager monitor')
    logging.debug('Configuration; throttle: %s seconds' % throttle)
    logging.debug('Configuration; monitored file: %s' % monitored_file)
    logging.debug('Configuration; cisis path: %s' % cisis_path)

    try:
        cisis = CISIS(cisis_path)
    except:
        exit()

    if not inspect_file(monitored_file):
        exit()
    
    while True:
        logging.info('Checking changes')

        if not CHECKSUMS.is_checksum_equal(monitored_file, open(monitored_file).read()):
            dispatcher(cisis.isis2json(monitored_file), collection)

        time.sleep(int(throttle))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Monitor for Title Manager changes"
    )

    parser.add_argument(
        '--monitored_file',
        '-f',
        help='Full path to the file that will be monitored, must be a MST file'
    )

    parser.add_argument(
        '--cisis_path',
        '-c',
        default='cisis',
        help='Full path to the cisis utilitary directory'
    )

    parser.add_argument(
        '--collection_acronym',
        '-a',
        choices=['scl', 'arg', 'sza'],
        help='Full path to the cisis utilitary directory'
    )

    parser.add_argument(
        '--throttle',
        '-t',
        default=THROTTLE_TIME,
        help='Sleep time or throttle for the monitor to check changes. Must be represented in seconds'
    )

    parser.add_argument(
        '--logging_file',
        '-o',
        help='Full path to the log file'
    )

    parser.add_argument(
        '--logging_level',
        '-l',
        default='DEBUG',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logggin level'
    )

    args = parser.parse_args()

    _config_logging(args.logging_level, args.logging_file)

    main(
        args.monitored_file,
        args.cisis_path,
        args.collection_acronym,
        throttle=args.throttle
    )