# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import json

# TODO make buttons in forms


class ZBSPipeline(models.Model):
    _inherit = ["mail.thread", "zbs.xport.mixin"]
    _name = "zbs.pipeline"
    _description = "Zync Pipeline"
    _order = "id desc"

    paused = fields.Boolean("Paused")
    major_version = fields.Integer("MAJOR", tracking=True)
    minor_version = fields.Integer("MINOR", tracking=True)
    patch_version = fields.Integer("PATCH", tracking=True)
    name = fields.Char("Name", required=True)
    line_ids = fields.One2many("zbs.pipeline.line", "pipeline_id", "Lines", copy=False)
    sequence_id = fields.Many2one(
        "ir.sequence",
        string="Sequence",
        default=lambda self: self.env.ref("zbsync.sequence_zbs_instance").id,
        xport_ignore=True,
    )
    tag_ids = fields.Many2many("zbs.pipeline.tag", string="Tags")
    cronjob_ids = fields.Many2many(
        "zbs.cronstart",
        "zbs_cronstart_zbs_pipeline_rel",
        "zbs_pipeline_id",
        "zbs_cronstart_id",
        string="Cronjobs",
        xport_ignore=True,
    )
    queuejob_channel = fields.Char("Queuejob Channel", default="root")
    queuejob_priority = fields.Integer("Queuejob Priority", default=10)
    limit_parallel_runs = fields.Integer("Limit Parallel Runs", default=0)
    keep_instances_for_days = fields.Integer("Keep Instances For Days", default=3)
    garbage_collect_failed_jobs = fields.Boolean(
        "Garbage Collect Failed Jobs", default=True
    )
    version_ids = fields.One2many(
        "zbs.pipeline.version", "pipeline_id", "Versions", xport_ignore=True
    )
    logoutput = fields.Selection(
        [
            ("odoo_logs", "Odoo-Logs"),
            ("db", "Database"),
        ],
        default="odoo_logs",
        required=True,
    )

    def snapshot(self):
        for rec in self:
            rec.version_ids = [(0, 0, {"content": json.dumps(rec.dump(), indent=4)})]

    @api.constrains("limit_parallel_runs")
    def _check_limit_parallel_runs(self):
        for rec in self:
            if rec.limit_parallel_runs < 0:
                raise ValidationError(_("Limit Parallel Runs must be at least 0."))

    def run_test(self):
        res = self._make_instance(test_mode=True)
        if self.env["zbs.tools"]._is_testing():
            return self.env["zbs.instance"].browse(res["res_id"])
        return res

    def start_from_ui_like_cronjob(self):
        return self._make_instance(test_mode=False, no_cron_start=False)

    def _make_instance(self, test_mode=None, no_cron_start=True):
        self.ensure_one()
        instance = self.start(
            data=None, test_mode=test_mode, no_cron_start=no_cron_start
        )
        self.env["zbs.tools"].commit()
        instance._start()

        if test_mode:
            batches = instance.next_line_id.batch_ids.filtered(
                lambda x: x.state == "failed"
            )
            if batches:
                return {
                    "view_type": "form",
                    "res_model": batches._name,
                    "domain": [("id", "in", batches.ids)],
                    "views": [(False, "list"), (False, "form")],
                    "type": "ir.actions.act_window",
                    "target": "current",
                }
        return {
            "view_type": "form",
            "res_model": instance._name,
            "res_id": instance.id,
            "views": [(False, "form")],
            "type": "ir.actions.act_window",
            "target": "current",
        }

    def show_lines(self):
        return {
            "name": _("Lines"),
            "view_type": "form",
            "res_model": "zbs.pipeline.line",
            "domain": [("pipeline_id", "=", self.id)],
            "context": {"default_pipeline_id": self.id},
            "views": [(False, "kanban")],
            "type": "ir.actions.act_window",
            "target": "current",
        }

    def show_instances(self):
        return {
            "name": _("Instances"),
            "view_type": "form",
            "res_model": "zbs.instance",
            "domain": [("pipeline_id", "=", self.id)],
            "views": [(False, "list"), (False, "form")],
            "type": "ir.actions.act_window",
            "target": "current",
        }

    def start(
        self,
        data,
        no_cron_start=False,
        initiated_by=None,
        environment=None,
        test_mode=False,
        zbs_environment=None,
    ):
        self.ensure_one()
        if no_cron_start and not initiated_by:
            initiated_by = "execute_and_run_in_code"
        assert initiated_by in [
            "cronjob",
            "fileupload",
            "button",
            "execute_and_run_in_code",
            None,
            "method_trigger",
            "webcall",
        ]
        instance = self.env["zbs.instance"].sudo().create({"pipeline_id": self.id})
        if environment:
            instance.environment = self.env["zebrooset"].dumps(environment)
        if data:
            instance.initial_data = self.env["zebrooset"].dumps(data)
        instance.origin = initiated_by
        instance.test_mode = test_mode
        instance.next_line_id = instance.line_ids.sorted()[0]
        instance.no_cron_start = no_cron_start
        if zbs_environment:
            instance.environment_id = zbs_environment
        return instance

    def add_worker(self):
        return {
            "view_type": "form",
            "res_model": "zbs.wiz.new.el",
            "views": [(False, "form")],
            "context": {
                "default_pipeline_id": self.id,
            },
            "type": "ir.actions.act_window",
            "target": "new",
        }

    def copy(self, defaults=None):
        self = self.with_context(nostart_stop=True, zync_import=True)
        res = super(ZBSPipeline, self).copy(defaults)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res._make_sure_startstop()
        return res

    def _make_sure_startstop(self):
        if self.env.context.get("nostart_stop"):
            return
        for rec in self:
            starters = rec.line_ids.filtered(lambda x: x.worker_id._name == "zbs.start")
            if not starters:
                start = self.env["zbs.start"].create({})
                rec.line_ids = [
                    [
                        0,
                        0,
                        {
                            "worker_id": f"{start._name},{start.id}",
                            "sequence": 999999,
                        },
                    ]
                ]
            stoppers = rec.line_ids.filtered(lambda x: x.worker_id._name == "zbs.stop")
            if not stoppers:
                stop = self.env["zbs.stop"].create({})
                rec.line_ids = [
                    [
                        0,
                        0,
                        {
                            "worker_id": f"{stop._name},{stop.id}",
                            "sequence": 999999,
                        },
                    ]
                ]

    def _resequence(self):
        for i, line in enumerate(self.line_ids.sorted()):
            if line.sequence != i:
                line.sequence = i

    def _add_worker(self, worker):
        self.line_ids = [
            [
                0,
                0,
                {
                    "worker_id": f"{worker._name},{worker.id}",
                    "sequence": 100,
                },
            ]
        ]

    def duplicate(self, defaults={}):
        wiz = self.env["zbs.dup.wizard"].create(
            {
                "src_pipeline_id": self.id,
            }
        )
        return {
            "view_type": "form",
            "res_model": wiz._name,
            "res_id": wiz.id,
            "views": [(False, "form")],
            "type": "ir.actions.act_window",
            "context": {
                "form_view_initial_mode": "edit",
            },
            "target": "new",
        }

    @api.model
    def _search_pipeline(self, name, kwparams):
        if not name:
            pipeline = kwparams.pop("pipeline")
        else:
            pipeline = (
                self.env["zbs.pipeline"]
                .search(
                    [
                        ("name", "=", name),
                    ]
                )
                .ensure_one()
            )
        return pipeline

    @api.model
    def start_in_background(self, name, data=None, **kwparams):
        # https://www.zebroo.de/knowledge/article/257
        pipeline = self._search_pipeline(name, kwparams)
        return pipeline.start(data=data, **kwparams)

    @api.model
    def start_and_execute(self, name, data=None, **kwparams):
        # https://www.zebroo.de/knowledge/article/257
        pipeline = self._search_pipeline(name, kwparams)
        kwparams["no_cron_start"] = True
        instance = pipeline.start(data=data, **kwparams)
        self.env.cr.commit()
        try:
            instance._complete_run()
            instance._raise_for_status()
        except:
            self.env.cr.rollback()
            instance.state = "failed"
            self.env.cr.commit()
            instance._raise_for_status()
        else:
            return instance
