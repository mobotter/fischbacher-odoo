# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).

from odoo import api, fields, models
from .zebrooset import ZebrooSet
import logging

RANGE_HELP = "like 1,2,3 or 1-3,8-5"
FILTER_HELP = "record.name != 'a', record.id > 50"


logger = logging.getLogger("zbs.pipeline")


class ZBSPipelineLine(models.Model):
    _inherit = ["zbs.xport.mixin"]
    _name = "zbs.pipeline.line"
    _description = "Zync Pipeline Line"
    _order = "sequence,id"
    _log_access = False

    name = fields.Char(compute="_compute_name")
    batchsize = fields.Integer("Batch Size")
    group_continue_here = fields.Char("Continue Here Group")
    abort_on_error = fields.Boolean(default=lambda self: True)

    pipeline_id = fields.Many2one(
        "zbs.pipeline",
        "Pipeline",
        required=False,
        ondelete="cascade",
        xport_ignore=True,
    )
    sequence = fields.Integer("Sequence")
    loglevel = fields.Selection(
        [
            ("debug", "Debug"),
            ("info", "Info"),
            ("warning", "Warning"),
            ("error", "Error"),
            ("critical", "Critical"),
        ],
        "Log Level",
        default="info",
    )
    condition = fields.Text("Condition", default="True")
    logged = fields.Text("Log")
    own_queuejob = fields.Boolean("Job", default=False)
    worker_id = fields.Reference(
        selection="_get_worker_selection", string="Worker", required=True, copy=False
    )
    worker_pipeline_ids = fields.Many2many(
        "zbs.pipeline",
        compute="_compute_worker_pipelines",
    )

    len_worker_pipeline_ids = fields.Integer(compute="_compute_worker_pipelines")
    ttype_name = fields.Char("Type", compute="_compute_typename")
    enabled = fields.Boolean("Enabled", default=True)
    continue_immediately = fields.Boolean("Continue immediatley", default=True)

    can_open_worker_detail = fields.Boolean(
        compute="_compute_can_open_worker_detai", store=False
    )

    keep_input_filter = fields.Char(
        "Keep Input Filter",
        help=(
            "* to keep source record; record.a.b.c to select specific data; "
            "can be semicolon separated; input.a.b.c; "
            "{'f1': input.f1}"
        ),
    )
    range = fields.Char("Input Range", help=RANGE_HELP)
    output_range = fields.Char("Output Range", help=RANGE_HELP)
    ffilter = fields.Char("Input Filter", help=FILTER_HELP)
    output_ffilter = fields.Char("Output Filter", help=FILTER_HELP)
    path_content = fields.Char(
        "Path Content",
        help=(
            "Input is a list of all batches."
            "Where to start iterating data from e.g. data[5].field1.records OR let "
            "zync iterate and extract data from record e.g. record.field1 and you get "
            "an array of that extracted"
        ),
    )
    retry_pattern = fields.Char(
        "Retry Pattern", help="e.g. 1,3,5,10,200 in seconds for each try"
    )
    batch_execution_in_order = fields.Boolean("Execute batches in order")
    queuejob_channel = fields.Char("Queuejob Channel")
    queuejob_priority = fields.Integer("Queuejob Priority", default=10)

    @api.depends("worker_id")
    def _compute_typename(self):
        for rec in self:
            rec.ttype_name = rec.worker_id._name

    def _get_worker_selection(self):
        return self.env["zbs.worker"].zbs_sub_classes_for_selection()

    @api.model
    def load_data(self, data):
        data = data or ""
        if not data:
            return None
        if data.startswith("ODOO:"):
            _, model, ids = data.split(":")
            ids = ids and map(int, ids.split(",")) or []
            return self.env[model].browse(ids)

        elif data.startswith("ZebrooSet:"):
            return ZebrooSet._loads(data.split("ZebrooSet:", 1)[1], env=self.env)
        elif isinstance(data, (list, dict)):
            return ZebrooSet(data)
        elif isinstance(data, str):
            return ZebrooSet._loads(data, env=self.env)
        else:
            raise NotImplementedError(data)

    @api.model
    def dump_data(self, data):
        if not isinstance(data, (models.Model, list, dict, ZebrooSet)):
            data = [data]

        if isinstance(data, models.Model):
            return f"ODOO:{data._name}:{','.join(map(str, data.ids))}"
        elif isinstance(data, (list, dict, ZebrooSet)):
            if isinstance(data, ZebrooSet):
                data = data._d
            return "ZebrooSet:" + ZebrooSet._dumps(None, content=data, env=self.env)
        else:
            raise NotImplementedError(data)

    def open_worker(self):
        obj = self.env[self.worker_id._name].browse(self.worker_id.id)
        return obj.open()

    def open_worker_detail(self):
        obj = self.env[self.worker_id._name].browse(self.worker_id.id)
        return obj.open()

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        if not self.env.context.get("zync_import"):
            # make sure there is start and end
            res.pipeline_id._make_sure_startstop()

            stoppers = res.pipeline_id.line_ids.filtered(
                lambda x: x.worker_id._name == "zbs.stop"
            )
            if stoppers[-1].sequence <= res.sequence:
                res.sequence, stoppers[-1].sequence = (
                    stoppers[-1].sequence,
                    res.sequence,
                )

            res.pipeline_id._resequence()

        return res

    def _copy_for_instance(self, instance):
        res = {
            "pipeline_id": self.pipeline_id.id,
            "sequence": self.sequence,
            "loglevel": self.loglevel,
            "own_queuejob": self.own_queuejob,
            "worker_id": f"{self.worker_id._name},{self.worker_id.id}",
            "enabled": self.enabled,
            "instance_id": instance.id,
            "original_line_id": self.id,
            "range": self.range,
            "output_range": self.output_range,
            "ffilter": self.ffilter,
            "output_ffilter": self.output_ffilter,
            "batchsize": self.batchsize,
        }
        return res

    def open_line(self, css_class=""):
        return {
            "name": self.worker_id.name,
            "type": "ir.actions.act_window",
            "view_type": "form",
            "res_model": self._name,
            "res_id": self.id,
            "views": [(False, "form")],
            "target": "new",
        }

    def ok(self):
        return {"type": "ir.actions.act_window_close"}

    def isinrange(self, index, the_range):
        if not the_range:
            return True
        for section in the_range.strip().split(","):
            section = section.strip().replace(" ", "")
            if "-" in section:
                start, end = section.split("-")
                if index >= int(start) and index <= int(end):
                    return True
            else:
                if index == int(section):
                    return True

    def _compute_can_open_worker_detai(self):
        for rec in self:
            rec.can_open_worker_detail = rec.worker_id.can_open_worker_detail

    def read(self, fields=None, load="_classic_read"):
        result = super().read(fields=fields, load=load)
        if self.env.context.get("opened_from_instance_line"):
            FIELDS = self.env["zbs.instance.line"].FIELDS_ONLY_UPDATED_IN_INSTANCE_LINE
            rec = (
                self.env["zbs.instance.line"]
                .browse(self.env.context["zbs_instance_line_id"])
                .with_context(opened_from_instance_line=False)
                .read(
                    FIELDS,
                )
            )
            for k in FIELDS:
                result[0][k] = rec[0][k]

        return result

    def write(self, vals):
        if self.env.context.get("opened_from_instance_line"):
            vals2 = {}
            for k in list(vals):
                if (
                    k
                    in self.env[
                        "zbs.instance.line"
                    ].FIELDS_ONLY_UPDATED_IN_INSTANCE_LINE
                ):
                    vals2[k] = vals[k]
                    vals.pop(k)
            if vals2:
                self.env["zbs.instance.line"].browse(
                    self.env.context["zbs_instance_line_id"]
                ).with_context(opened_from_instance_line=False).write(vals2)

        res = super().write(vals)
        # if not self.env.context.get("zync_import"):
        # self.pipeline_id._resequence()
        return res

    def _resequence(self):
        for i, line in enumerate(self.line_ids.sorted()):
            if line.sequence != i:
                line.sequence = i

    def unlink(self):
        for rec in self:
            if not self.env.context.get("zbs_worker_unlink"):
                others = self.search([]).filtered(
                    lambda x: x.worker_id == rec.worker_id and x.id != rec.id
                )
                if not others:
                    rec.worker_id.unlink()

        return super().unlink()

    def _compute_name(self):
        for rec in self:
            if not rec.pipeline_id:
                rec.name = "-"
                continue
            rec.name = (
                f"{rec.pipeline_id.name}:"
                f"{rec.sequence}:{rec.worker_id._name}:{rec.worker_id.name}"
            )

    @api.depends("worker_id")
    def _compute_worker_pipelines(self):
        for rec in self:
            pipelines = (
                self.env["zbs.pipeline.line"]
                .search(
                    [("worker_id", "=", f"{rec.worker_id._name},{rec.worker_id.id}")]
                )
                .pipeline_id
            )
            rec.worker_pipeline_ids = [[6, 0, pipelines.ids]]
            rec.len_worker_pipeline_ids = len(pipelines)
