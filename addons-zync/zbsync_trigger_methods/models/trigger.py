# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import models


class TriggerMethodHook(models.Model):
    _inherit = ["zbs.trigger", "method_hook.trigger.mixin", "zbs.xport.mixin"]
    _name = "zbs.trigger.methodhook"
    _description = "Event Hook on methods/events"

    def _trigger(self, instances, args_packed, method):
        self._start_by_methodhook(instances, args_packed, method)

    def _start_by_methodhook(self, records, args, method):
        pipeline = self.pipeline_id
        if not pipeline:
            return
        for record in records:
            environment = self._prepare_environment(record, args, method)
            instance = pipeline.start(
                record,
                initiated_by="method_trigger",
                environment=environment,
            )
            if instance._is_using_queuejobs():
                instance._delay_instance(enabled=True)

    def _prepare_environment(self, record, args, method):
        environment = {
            "args": args["args"],
            "kwargs": args["kwargs"],
            "method": method,
            "model": record._name,
            "ids": record.ids,
        }
        if method == "write":
            try:
                _fields = args["args"][1].keys()
            except IndexError:
                _fields = args["args"][0].keys()
            environment["fields"] = sorted(_fields)
        return environment
