# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).

from odoo import fields, models
from .zebrooset import ZebrooSet
from odoo.addons.zbsync.models.zebrooset import ZebrooSet, _WrappedList, _WrappedDict


# this is embedded in a pipeline element
class ZBSWorker(models.AbstractModel):
    """
    Call on iteration or where applicable:

    keep_input = self._extract_input_information(record)
    # merge it into the result

    """

    _inherit = ["zbs.xport.mixin", "mail.thread"]
    _name = "zbs.worker"
    _description = "Zync Worker"

    name = fields.Char("Name")
    can_open_worker_detail = fields.Boolean(compute="_compute_can_open_worker_detail")
    can_show_heartbeat = fields.Boolean(
        compute="_compute_can_show_heartbeat", xport_ignore=True
    )
    comment = fields.Text("Comment")
    documentation = fields.Text("Documentation")
    pipeline_ids = fields.Many2many("zbs.pipeline", compute="_compute_pipelines")
    used_in_more_pipelines = fields.Boolean(compute="_compute_pipelines")
    post_process = fields.Text(
        "Post Process",
        help="Final processing of the retrieved data, before passing to next worker",
    )

    def _compute_pipelines(self):
        for rec in self:
            pipelines = (
                self.env["zbs.pipeline.line"]
                .search([("worker_id", "=", f"{rec._name},{rec.id}")])
                .pipeline_id
            )
            rec.pipeline_ids = pipelines
            rec.used_in_more_pipelines = len(pipelines) > 1

    def name_get(self):
        res = []
        for rec in self:
            if not rec.exists():
                res.append((False, "deleted"))
            else:
                res.append((rec.id, rec.name))
        return res

    def _compute_can_show_heartbeat(self):
        for rec in self:
            rec.can_show_heartbeat = bool(rec.env.context.get("zbs_instance_id"))

    def heartbeat(self):
        instance = self.env["zbs.instance"].browse(
            self.env.context.get("zbs_instance_id")
        )
        worker_line = instance.line_ids.filtered(lambda x: x.worker_id == self)
        if worker_line:
            worker_line.make_current()
        instance.heartbeat_ui()

    def is_start(self):
        return False

    def is_end(self):
        return False

    def _get_pipelines(self):
        self.ensure_one()
        lines = self.env["zbs.pipeline.line"].search(
            [("worker_id", "=", f"{self._name},{self.id}")]
        )
        return lines

    @property
    def can_lock_resources(self):
        return False

    def get_lock_resources(self, instance, data, errors=None):
        locks = []

        def add_lock(resource):
            locks.append(resource)

        self.with_context(zbs_lock_resources=add_lock).process(
            instance, data, errors=errors
        )
        return locks

    def process(self, instance, data, func=None, errors=None):
        def default_func(instance, index, record, data, errors=None):
            return self.process_record(instance, index, record, data, errors=errors)

        func = func or default_func

        res = self._process_worker_base(instance, data, func, errors=errors)
        return res

    def _iterate_data(self, data):
        for index, record in self.env["zebrooset"].iterate(data):
            if hasattr(record, "_zbs_unwrap"):
                record = record._zbs_unwrap()
            yield index, record

    def _process_worker_base(self, instance, data, func, errors=None):
        from ..exceptions import SkipRecord

        result = []
        for index, record in self._iterate_data(data):
            try:
                current = func(instance, index, record, data, errors=errors)
            except SkipRecord:
                continue
            except Exception as ex:
                dumped_record = self.env["zebrooset"].dumps(record)
                ex.zbs_record = dumped_record
                raise
            self._apply_keep_input(index, record, data, current)

            if isinstance(current, list):
                result += current
            elif isinstance(current, ZebrooSet) and isinstance(current._d, list):
                result += current._d
            elif isinstance(current, _WrappedList) and isinstance(current._l, list):
                result += current._l
            else:
                result.append(current)
        return instance.Result(result)

    def process_record(self, instance, index, record, data, errors=None):
        raise NotImplementedError("Please implement process record")

    def _do_post_process(self, process_result):
        if not self.post_process:
            return process_result

        data = process_result.data
        data = self.env["zebrooset"].rs(data)
        eval_result = self._eval_expression(
            self.post_process,
            0,
            data,
            data,
            input=self.env.context.get("zbs_prepared_input_data"),
        )
        if eval_result is None:
            process_result.data = data
        else:
            process_result.data = eval_result
        return process_result

    def open_action(self):
        self.ensure_one()
        return {
            "view_type": "form",
            "res_model": self._name,
            "res_id": self.id,
            "views": [(False, "form")],
            "type": "ir.actions.act_window",
            "target": "current",
            "context": {
                "zbs_instance_id": self.env.context.get("zbs_instance_id"),
            },
        }

    def _apply_keep_input(self, index, record, input_data, result_records):
        kept = self._keep_input(index, record, input_data)
        if isinstance(result_records, (dict, list)):
            result_records = self.env["zebrooset"].rs(result_records)
        if not kept:
            return
        if not isinstance(
            result_records, (list, _WrappedList, dict, _WrappedDict, ZebrooSet)
        ):
            # case: web worker returns a bytes; this can be transformed by post process
            # to a dictionary: content: <bytes>; if this is not done, then a merge of keep
            # input is simply not possible. Raise error in that case
            raise Exception(f"Could not apply keep input filter on {result_records}")
        for index, rec in result_records._iterate_records():
            self._apply_keep_input_merge_record(rec, kept)

    def _apply_keep_input_merge_record(self, rec, kept):
        rec._merge(kept)

    def _keep_input(self, index, record, input_data):
        input_data = self.env.context["zbs_prepared_input_data"]
        batch = self.env.context["zbs_batch"]
        line = self.env.context["zbs_pipeline"]
        keep_input_filter = self.env.context.get("keep_input_filter")
        assert line._name in ["zbs.instance.line", "zbs.instance.line.light"]
        if not keep_input_filter:
            return {}
        if keep_input_filter == "*":
            return input_data
        if keep_input_filter == "record":
            return record
        if not keep_input_filter:
            return {}
        keep_filter = keep_input_filter.replace(";", ",")
        data = input_data
        if isinstance(data, (list, dict)):
            data = ZebrooSet(data)

        if "," in keep_filter:
            parts = list(map(lambda x: x.strip(), keep_filter.split(",")))
        else:
            parts = [keep_filter]
        result = self._keep_input_eval(parts, record, input_data, index)
        return result

    def _keep_input_eval(self, filters, record, input_data, index):
        result = {}
        for part in filters:
            partresult = self.env["zbs.tools"]._exec_get_result(
                part,
                {
                    "record": record,
                    "data": input_data,
                    "input": input_data,
                    "index": index,
                },
            )
            try:
                zpart = ZebrooSet(partresult)
            except:
                zpart = None
            if not zpart or not isinstance(zpart._as_python_object(), dict):
                name = part.split(".")[-1]
                partresult = {name: partresult}
            result = self.env["zebrooset"].rs(result)
            result._merge(partresult)
            result = result._d
        return result

    def _compute_can_open_worker_detail(self):
        for rec in self:
            rec.can_open_worker_detail = False

    def open(self):
        # fallback action
        self.ensure_one()
        return {
            "name": self.name,
            "view_type": "form",
            "res_id": self.id,
            "res_model": self._name,
            "views": [(False, "form")],
            "type": "ir.actions.act_window",
            "target": "current",
        }

    def unlink(self):
        for rec in self:
            lines = self.env["zbs.pipeline.line"].search(
                [("worker_id", "=", f"{rec._name},{rec.id}")]
            )
            lines.with_context(zbs_worker_unlink=True).unlink()

        return super().unlink()

    def _eval_expression(
        self, text, index, record, data, input, expects_string_if_oneline=False
    ):
        self.ensure_one()
        path = (text or "").strip()
        instance = self.env.context.get("zbs_instance")
        _globals = instance._get_default_objects(
            {
                "index": index,
                "record": record,
                "input": input,
                "data": data,
            }
        )

        if _globals.get("environment"):
            company = self.env["zbs.environment"]._extract_company(
                _globals["environment"]
            )
            if company:
                self = self.with_company(company)

        return self.env["zbs.tools"]._eval_oneliner_or_code(
            path, _globals, expects_string_if_oneline=expects_string_if_oneline
        )
