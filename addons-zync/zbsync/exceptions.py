# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).


class ConfigurationError(Exception):
    pass


class BatchFailed(Exception):
    pass


class RetryInNextTimeframe(Exception):
    pass


class ZBSPipelineException(Exception):
    def __init__(self, code, name, error_records=None, *args, **kwargs):
        super().__init__(name)
        self.code = code


class SkipRecord(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


try:
    from odoo.addons.queue_job.exception import RetryableJobError
except:

    class RetryableJobError(Exception):
        def __init__(self, msg, seconds=None, ignore_retry=False):
            super().__init__(msg)
            self.seconds = seconds
            self.ignore_retry = ignore_retry
