import logging


class DistrictEuroLoggingHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        logging.Handler.__init__(self, level)

    def emit(self, record):
        try:
            # need to import this here otherwise it causes a circular
            # reference and doesn't work
            from core.models import SystemLog
            if record and hasattr(record, 'levelname') and record.levelname is not None:
                log_level = record.levelname
                log_message = record.getMessage()
                SystemLog.objects.create(level=log_level, message=log_message)
        except Exception as e:
            print "[Database Logging failed] ::" + str(e)
        return
