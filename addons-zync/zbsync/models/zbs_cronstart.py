# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).

from odoo import _, api, fields, models, Command
from odoo.exceptions import UserError


class ZBSCron(models.Model):
    _inherit = "zbs.start"
    _name = "zbs.cronstart"
    _description = "trigger:cronjob"

    name = fields.Char(required=True)
    cronjob_ids = fields.One2many("ir.cron", "zbs_crontrigger_id", string="Cronjobs")
    cronstart_pipeline_ids = fields.Many2many(
        "zbs.pipeline",
        "zbs_cronstart_zbs_pipeline_rel",
        "zbs_cronstart_id",
        "zbs_pipeline_id",
        string="Pipelines",
        xport_ignore=True,
        readonly=False,
    )
    no_double_starts = fields.Boolean("Wait Finished", default=True)

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for rec in res:
            if not rec.cronstart_pipeline_ids:
                raise UserError(
                    _("Please select at least one pipeline for cron actions to create.")
                )
        return res

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)

        if self.env.context.get("model") == "zbs.pipeline":
            params = self.env.context
        else:
            params = self.env.context.get("params", {})

        if params.get("model") == "zbs.pipeline":
            res.setdefault("cronstart_pipeline_ids", [])
            pipeline = (
                self.env["zbs.pipeline"]
                .sudo()
                .browse(params.get("id"))
            )
            res["cronstart_pipeline_ids"] = [Command.set(pipeline.ids)]
        return res

    @api.model
    def _start(self, *args, zbs_environment=None, **kwargs):
        for rec in self:
            for pipe in rec.cronstart_pipeline_ids:
                if rec.no_double_starts:
                    if self.env["zbs.instance"].search_count(
                        [
                            ("state", "in", ["pending", "running"]),
                            ("pipeline_id", "=", pipe.id),
                        ]
                    ):
                        continue
                instance = pipe.start(
                    {},
                    initiated_by="cronjob",
                    environment={
                        "cronstart": True,
                    },
                    zbs_environment=zbs_environment,
                )
                instance._delay_instance(enabled=True)

    def open_cronjobs(self):
        self.ensure_one()
        jobs = self.env["ir.cron"].search([("zbs_crontrigger_id", "=", self.id)])
        if not jobs:
            vals = jobs.with_context(
                active_model=self._name, active_id=self.id
            ).default_get([])
            vals["name"] = f"Cron job for {self.name}"
            vals["interval_type"] = "hours"
            vals["model_id"] = (
                self.env["ir.model"]
                .search([("model", "=", self._name)])
                .ensure_one()
                .id
            )
            vals["zbs_crontrigger_id"] = self.id
            jobs = jobs.create(vals)
        return {
            "name": self.name,
            "view_type": "form",
            "res_model": "ir.cron",
            "domain": [("zbs_crontrigger_id", "in", self.ids)],
            "views": [(False, "list"), (False, "form")],
            "type": "ir.actions.act_window",
            "target": "current",
            "context": {
                "default_zbs_crontrigger_id": self.id,
                "default_active": True,
                "active_model": self._name,
                "active_id": self.id,
            },
        }

    @api.constrains("name")
    def _update_names_in_cronjobs(self):
        for rec in self:
            if rec.cronjob_ids:
                rec.cronjob_ids.sudo().write({"name": rec.name})
