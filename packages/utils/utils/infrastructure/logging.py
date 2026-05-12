import logging

# we put most info in 'extra' argument of log functions for logstash, 
# but for console logger by default doesn't show 'extra' fields, 
# so we create a custom formatter to extract all additional fields to a
# console-only attribute and access it in format string as %(console_extra)s.
# Using the name "extra" here breaks logstash_async because that formatter
# expects its own structured "extra" object.
class ExtraFieldsFormatter(logging.Formatter):
    def format(self, record):
        # standard LogRecord attributes
        standard_attrs = logging.LogRecord(
            name='', level=0, pathname='', lineno=0,
            msg='', args=(), exc_info=None
        ).__dict__.keys()

        # extract extra fields
        extra_lines = {
            f"\n\t\t  {k}: {v}" for k, v in record.__dict__.items()
            if k not in standard_attrs
        }

        record.console_extra = ''.join(extra_lines)  # attach for console formatter
        return super().format(record)
