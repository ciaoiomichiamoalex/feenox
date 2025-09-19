from datetime import datetime

import feenox
from core import get_logger

logger = get_logger(feenox.PATH_LOG)

if __name__ == '__main__':
    job_begin = datetime.now()

    try:
        feenox.save_toll_groups()

        # save new daily tolls
        feenox.save_tolls('P', job_begin=job_begin)
        # save new invoice tolls
        feenox.save_tolls('D', job_begin=job_begin)

        # download invoice documents
        feenox.save_documents('FATTURA', job_begin=job_begin)
        feenox.save_documents('ALLEGATO_FATTURA', job_begin=job_begin)
        feenox.save_documents('ALLEGATO_FATTURA_CSV', job_begin=job_begin)
        feenox.save_documents('ALLEGATO_FATTURA_TXT', job_begin=job_begin)
    except Exception: logger.exception('unhandled exception')
