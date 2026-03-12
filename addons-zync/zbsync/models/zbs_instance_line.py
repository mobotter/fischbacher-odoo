# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).

from odoo import api, fields, models, tools
import logging
from .zebrooset import ZebrooSet
from .zbs_pipeline_line import RANGE_HELP

logger = logging.getLogger("ZBSLog")


class InstanceLine(models.Model):
    _inherit = "zbs.pipeline.line"
    _name = "zbs.instance.line"
    _description = "Zync Instance Line"
    _order = "sequence,id"
    _log_access = False

    FIELDS_ONLY_UPDATED_IN_INSTANCE_LINE = [
        "range",
        "output_range",
        "ffilter",
        "output_ffilter",
    ]

    create_date = fields.Datetime(default=lambda self: fields.Datetime.now())
    sequence = fields.Integer(related="original_line_id.sequence", store=True)
    batches = fields.Text(compute="_compute_batches", string="Batch(es)")
    batch_ids = fields.One2many("zbs.instance.line.batch", "line_id", string="Batches")
    active = fields.Boolean(default=True)

    is_current = fields.Boolean(string="Is Current", compute="_compute_is_current")
    original_line_id = fields.Many2one("zbs.pipeline.line")
    instance_id = fields.Many2one("zbs.instance", ondelete="cascade")
    range = fields.Char("Input Range", help=RANGE_HELP)
    output_range = fields.Char("Output Range", help=RANGE_HELP)
    ffilter = fields.Char()
    output_ffilter = fields.Char()
    batchsize = fields.Integer()
    keep_input_filter = fields.Char(
        related="original_line_id.keep_input_filter", readonly=False
    )
    continue_immediately = fields.Boolean(
        compute="_compute_continue_immediately", store=True
    )
    processed_records = fields.Integer("Processed Records", compute="_compute_counter")
    name = fields.Char(related="original_line_id.name")
    path_content = fields.Char(related="original_line_id.path_content")
    generated_batches = fields.Boolean("Generated Batches")
    has_failed = fields.Boolean(compute="_compute_batches")
    only_success = fields.Boolean(compute="_compute_batches")
    abort_on_error = fields.Boolean(
        related="original_line_id.abort_on_error", default=None
    )
    retry_pattern = fields.Char(related="original_line_id.retry_pattern")

    @api.depends("original_line_id", "original_line_id.continue_immediately")
    def _compute_continue_immediately(self):
        # as related did not work in version 11.0
        for rec in self:
            rec.continue_immediately = rec.original_line_id.continue_immediately

    def _compute_counter(self):
        count = {}
        with self.env["zbs.tools"].new_env() as env:
            for rec in self:
                id = rec.id
                if isinstance(id, models.NewId):
                    id = id.origin
                env.cr.execute(
                    "select id from zbs_instance_line_batch where line_id = %s",
                    (id,),
                )
                batch_ids = [x[0] for x in env.cr.fetchall()]
                env.cr.execute(
                    "select sum(amount) from zbs_batch_counter where batch_id in %s",
                    (tuple(batch_ids + [0]),),
                )
                count[rec.id] = env.cr.fetchone()[0]
        for rec in self:
            rec.processed_records = count[rec.id]

    def _reset_processed(self, can_commit=False):
        for rec in self:
            inst = rec.instance_id
            with self.env["zbs.tools"].pglock(f"{inst._name}:{inst.id}_batches"):
                batches = self.env["zbs.instance.line.batch"].search(
                    [("line_id", "=", rec.id)]
                )
                BATCH_SIZE = 20
                done = 0
                for batch in tools.split_every(BATCH_SIZE, batches.ids):
                    logger.debug(
                        f"Deleting batches {BATCH_SIZE} done: {done} to go {len(batches.ids) - done}"
                    )
                    done += len(batch)
                    batch = batches.browse(batch).unlink()
                    if can_commit:
                        self.env["zbs.tools"].commit()
                rec.generated_batches = False
                if can_commit:
                    self.env["zbs.tools"].commit()

    @api.depends("instance_id.next_line_id")
    def _compute_is_current(self):
        for rec in self:
            rec.is_current = rec.instance_id.next_line_id == rec

    def _make_current(self):
        self.ensure_one()
        self.instance_id.state = "pending"
        self.instance_id.next_line_id = self
        self.instance_id.prev_line_override_id = False

    def _get_lines_after(self):
        passed = False
        for line in self.instance_id.line_ids.sorted():
            if line == self:
                passed = True
                continue
            if passed:
                yield line

    def make_current(self):
        self._reset_processed(can_commit=True)
        for line in list(self._get_lines_after()):
            line._reset_processed(can_commit=True)
        self._make_current()
        return True

    def open_logs(self):
        # TODO
        return self.show_data()
        self.ensure_one()
        logs = self.mapped("batch_ids.log_ids")
        if not logs:
            return False
        return {
            "type": "ir.actions.act_window",
            "name": "Logs",
            "res_model": logs._name,
            "res_id": logs[0].id,
            "views": [(False, "form")],
            "target": "new",
            "flags": {
                "form": {
                    "action_buttons": False,
                    "initial_mode": "view",
                }
            },
        }

    def open_batches(self):
        self.ensure_one()
        if len(self.batch_ids) == 1:
            return {
                "view_type": "form",
                "res_model": self.batch_ids._name,
                "res_id": self.batch_ids.id,
                "views": [(False, "form")],
                "type": "ir.actions.act_window",
                "target": "new",
            }
        return {
            "type": "ir.actions.act_window",
            "name": "Batches",
            "res_model": self.batch_ids._name,
            "domain": [("line_id", "=", self.id)],
            "views": [(False, "list"), (False, "form")],
            "target": "current",
        }

    def open_logs_list(self):
        self.ensure_one()
        logs = self.mapped("batch_ids.log_ids")
        if not logs:
            return False
        return {
            "type": "ir.actions.act_window",
            "name": "Logs",
            "res_model": logs._name,
            "domain": [("line_id", "=", self.id)],
            "views": [(False, "list"), (False, "form")],
            "target": "current",
        }

    def log(self, message, level=None):
        logoutput = self.env.context.get("zbs_logoutput", None)

        if not logoutput:
            return

        if logoutput == "odoo_logs":
            self._log_odoologs(message, level)
        elif logoutput == "database":
            self._log_database(message, level)
        else:
            raise NotImplementedError(logoutput)

    def _log_odoologs(self, message, level):
        level_as_int = getattr(logging, level.upper())
        logger.log(level_as_int, message)

    def _log_database(self, message, level):
        Tools = self.env["zbs.tools"]
        level = level or "info"
        levels = list(map(lambda x: x[0], self._fields["loglevel"].selection))
        index = levels.index(level)
        index_crit = levels.index(self.loglevel)
        instance = self.instance_id
        logger.info(message)
        if index < index_crit and not instance.test_mode:
            return

        with self.env["zbs.tools"].new_env(enabled=True) as env:
            self.with_env(env)._append_log_text(message)

            if self.env.context.get("zbs_instance_devmode") or level == "error":
                instance.with_env(env).sudo().message_post(
                    body=str(message)[:1024],
                )

    def _append_log_text(self, message):
        self.logged = (self.logged or "") + (message or "") + "\n"

    def open_line(self, css_class=""):
        line = self.original_line_id
        if "open_batches" in css_class:
            return self.open_batches()
        return {
            "name": line.worker_id.name,
            "type": "ir.actions.act_window",
            "view_type": "form",
            "res_model": line._name,
            "res_id": line.id,
            "views": [(False, "form")],
            "target": "new",
            "context": {
                "opened_from_instance_line": 1,
                "zbs_instance_line_id": self.id,
            },
        }

    @api.depends("batch_ids", "batch_ids.state")
    def _compute_batches(self):
        for rec in self:
            states = {}
            for batch in rec.batch_ids:
                states.setdefault(batch.state, 0)
                states[batch.state] += 1
            text = []
            for state in ["todo", "failed", "success"]:
                text.append(f"{state}: {states.get(state, 0)}")
            rec.batches = " ".join(text)

            rec.has_failed = states.get("failed", 0) > 0
            rec.only_success = not states.get("todo") and not states.get("failed")

    def _get_errors(self):
        self.ensure_one()
        exceptions = []
        for i, batch in enumerate(self.batch_ids.filtered(lambda x: x.err_desc)):
            batch_data = batch._get_exceptions()
            exceptions = self._append_data(i, exceptions, batch_data)

        return self.env["zebrooset"].rs(exceptions)

    def _get_data(self):
        self.ensure_one()
        data = []
        for i, batch in enumerate(
            self.batch_ids.filtered(lambda x: x.state == "success")
        ):
            batch_data = batch._get_data()

            data = self._append_data(i, data, batch_data)

        if self.output_range or self.output_ffilter:
            data = self.instance_id._filter_records(
                data, self.output_range, self.output_ffilter
            )

        if isinstance(data, models.Model):
            return data
        return self.env["zebrooset"].rs(data)

    @api.model
    def _append_data(self, index, container, item):
        if isinstance(item, ZebrooSet):
            if isinstance(item._as_python_object(), dict):
                item = ZebrooSet([item._as_python_object()])
            container += item
            return container

        elif isinstance(item, models.Model):
            if index == 0:
                return item
            else:
                container |= item
                return container

        elif item is None:
            return [None]
        else:
            raise NotImplementedError(item)

    def _get_prev_line(self):
        self.ensure_one()
        line_ids = self.instance_id.line_ids.sorted().ids
        idx = line_ids.index(self.id)
        if not idx:
            return self.env[self._name]
        return self.browse(line_ids[idx - 1])

    def show_data(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": f"/zync/instance_line/data/{self.id}",
            "target": "new",
        }

    @api.model
    def _has_condition_code(self):
        condition_code = self.original_line_id.condition
        return condition_code and condition_code != "True"

    @api.model
    def _eval_condition(self, data):
        condition_code = self.original_line_id.condition
        condition = True
        if self._has_condition_code():
            condition = self.env["zbs.tools"]._exec_get_result(
                condition_code, {"input": data, "data": data}
            )
        return condition
