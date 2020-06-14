import os
import sys
import logging
from time import strftime, gmtime

log = logging.getLogger('Fitness_Pose_Machine')

output_dir = './output'

_LOG_LVLS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}


def set_logger(level='debug'):
    """
    Console and output file logger.
    """
    _format = '[%(process)d] %(asctime)s %(levelname)5s %(name)-20s %(message)s'

    log.setLevel(_LOG_LVLS[level.upper()])
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(_LOG_LVLS[level.upper()])
    console_handler.setFormatter(logging.Formatter(_format))
    log.addHandler(console_handler)

    filename = os.path.join(output_dir, "/{}_{}.log".format(strftime("%Y%m%d_%H%M%S", gmtime()), level.upper()))
    file_handler = logging.FileHandler(filename)
    file_handler.setLevel(_LOG_LVLS[level.upper()])
    file_handler.setFormatter(logging.Formatter(_format))
    log.addHandler(file_handler)


