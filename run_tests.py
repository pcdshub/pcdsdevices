#!/usr/bin/env python
import sys
import os
import logging
from logging.handlers import TimedRotatingFileHandler
import pytest

if __name__ == '__main__':
    # Show output results from every test function
    # Show the message output for skipped and expected failures
    args = ['-v', '-vrxs']

    # Add extra arguments
    if len(sys.argv) > 1:
        args.extend(sys.argv[1:])

    # Ignore live tests unless given the live keyword
    if '--live' in args:
        args.remove('--live')
        args.append('tests_live')
    else:
        args.append('--ignore=tests_live')

    txt = 'pytest arguments: {}'.format(args)
    print(txt)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    log_filename = os.path.join(os.path.dirname(__file__), 'debug.log')
    handler = TimedRotatingFileHandler(log_filename, when='d', interval=1,
                                       backupCount=7)
    formatter = logging.Formatter(fmt=('%(asctime)s '
                                       '%(name)-20s '
                                       '%(levelname)-8s '
                                       '%(message)s'),
                                  datefmt='%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    logger = logging.getLogger(__name__)
    logger.info(txt)

    sys.exit(pytest.main(args))
