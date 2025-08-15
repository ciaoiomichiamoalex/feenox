from datetime import datetime

import feenox
from core import get_logger

logger = get_logger(feenox.PATH_LOG)

if __name__ == '__main__':
    job_begin = datetime.now()

    try:
        feenox.save_toll_groups()

        feenox.save_tolls('P', job_begin=job_begin)
        feenox.save_tolls('D', job_begin=job_begin)

        feenox.save_documents('FATTURA', job_begin=job_begin)
    except Exception: logger.exception('unhandled exception')
