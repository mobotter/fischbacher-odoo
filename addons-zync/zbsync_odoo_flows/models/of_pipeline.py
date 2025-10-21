# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import api, fields, models


class Pipeline(models.Model):
    _inherits = {"of.base.item": "item_id"}
    _inherit = ["of.base.item.abstract"]
    _name = "of.zync.pipeline"
    _description = "Flow for ZBS Pipeline"

    pipeline_id = fields.Many2one("zbs.pipeline")
    run_type = fields.Selection(
        [("complete_run", "Complete Run"), ("delayed_run", "Delayed Run")]
    )
    zbs_instance_id = fields.Many2one(
        "zbs.instance", compute="_compute_zbs_instance", store=False
    )

    @api.depends_context("instance_id")
    def _compute_zbs_instance(self):
        for rec in self:
            rec.zbs_instance_id = False
            if self.env.context.get("instance_id"):
                ofinstance = self.env["of.instance"].browse(
                    self.env.context["instance_id"]
                )
                instance_item = ofinstance.get_item(self._name, self.id)
                if instance_item:
                    mt = instance_item.restore_metadata()
                    if mt.get("instance_id"):
                        rec.zbs_instance_id = mt["instance_id"]

    @api.onchange("pipeline_id")
    def _changed_pipe(self):
        for rec in self:
            rec.name = rec.pipeline_id.name

    @api.depends_context("active_model", "active_id")
    def _compute_custom_data_repr(self):
        for rec in self:
            rec.custom_data_repr = ""
        if self.env.context.get("active_model") == "of.instance.item":
            instance_item = (
                self.env["of.instance.item"]
                .sudo()
                .browse(self.env.context["active_id"])
            )
            for rec in self:
                zbinstance = self._get_zbs_instance(instance_item)
                if zbinstance:
                    name = (
                        f"{zbinstance.name}\n{zbinstance.next_line_id.name_get()[0][1]}"
                    )
                    rec.custom_data_repr = name

    def _zbs_get_previous_data(self, instance_item):
        return self.incoming_ids._zbs_get_previous_data(instance_item)

    def _heartbeat(self, instance_item, additional_data):
        super()._heartbeat(instance_item, additional_data)

        metadata = instance_item.restore_metadata()

        if not metadata.get("instance_id"):
            previous_data = self._zbs_get_previous_data(instance_item)
            zbinstance = self.pipeline_id.start(previous_data)
            metadata["instance_id"] = zbinstance.id
            instance_item.store_metadata(metadata)
            self.env.cr.commit()

        zbinstance = self.env["zbs.instance"].browse(metadata["instance_id"])
        done = zbinstance.state in ["success", "failed"]
        item = self.item_id.ref
        if item.run_type == "complete_run" or not item.run_type:
            if not done:
                with self.env["zbs.tools"].new_env(
                    enabled=True,
                ) as env:
                    zbinstance.with_env(env).with_context(
                        zbs_no_async_run=True
                    )._complete_run()
        elif item.run_type == "delayed_run":
            zbinstance._delay_instance()
        else:
            raise NotImplementedError(item.run_type)

        if zbinstance.state == "failed":
            instance_item.instance_id.abort()
        elif zbinstance.state == "success":
            instance_item._goto_next()

    @api.model
    def _get_zbs_instance(self, instance_item):
        data = instance_item.restore_metadata()
        if data.get("instance_id"):
            zbinstance = self.env["zbs.instance"].sudo().browse(data["instance_id"])
            return zbinstance
        return self.env["zbs.instance"].sudo()

    @api.model
    def _has_done_pipeline(self, instance_item):
        zbinstance = self._get_zbs_instance(instance_item)
        if zbinstance and zbinstance.state == "success":
            return True
        return False
