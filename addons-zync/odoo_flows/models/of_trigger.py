from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.tools.safe_eval import safe_eval

# from odoo.addons.queue_job.job import job


class Trigger(models.Model):
    _inherit = ["of.base.item.abstract", "of.mixin.code"]
    _inherits = {"of.base.item": "item_id"}
    _name = "of.trigger"
    _description = "Flows Trigger"

    method_trigger_ids = fields.One2many("of.trigger.methodhook", "trigger_id")
    trigger_by_code = fields.Boolean("Trigger By Code")

    def _start_by_methodhook(self, records):
        self = self.sudo()

        for record in records:
            self._start_new_flow_or_continue_existing(record)

    def _has_code(self):
        self.write({"has_code": True})

    def _heartbeat(self, odoo_instance=None, additional_data=None):
        self.ensure_one()
        if not self.trigger_by_code:
            return
        odoo_instances = self._eval()
        if not odoo_instances:
            return

        if not isinstance(odoo_instances, models.BaseModel):
            raise Exception("Requires odoo instances to be returned")

        def refify(odoo_instance):
            return f"{odoo_instance._name},{odoo_instance.id}"

        refs = list(map(refify, odoo_instances))

        running_flows = (
            self.env["of.instance"]
            .with_context(prefetch_fields=False)
            .search(
                [
                    ("active", "=", True),
                    ("flow_id", "=", self.item_id.flow_id.id),
                    ("initial_odoo_instance", "in", refs),
                ]
            )
        )
        running_refs = running_flows.mapped("initial_odoo_instance")

        unbound_refs = list(filter(lambda x: x not in running_refs, refs))
        bound_refs = list(filter(lambda x: x in running_refs, refs))

        def _ref2instance(ref):
            model, id = ref.split(",")
            id = int(id)
            return self.env[model].browse(id)

        for ref in bound_refs:
            ref = _ref2instance(ref)
            if self.item_id.outgoing_ids.filtered(
                lambda x: x.to_id.ref._name != "of.start"
            ):
                self._continue_in_running_flow(ref)
                if not self._is_testing():
                    self.env.cr.commit()

        for ref in unbound_refs:
            ref = _ref2instance(ref)
            if self.item_id.outgoing_ids.filtered(
                lambda x: x.to_id.ref._name == "of.start"
            ):
                self._start_new_flow(ref)
                if not self._is_testing():
                    self.env.cr.commit()

    def _continue_in_running_flow(self, odoo_instance):
        ref = f"{odoo_instance._name},{odoo_instance.id}"
        instances = self.env["of.instance"].search(
            [
                ("initial_odoo_instance", "=", ref),
            ]
        )
        for instance in instances:
            triggers = instance.item_ids.filtered(
                lambda x: x.has_cursor and x.item_id.ref == self
            )

            for trigger in triggers:
                trigger._goto_next()

    def _start_new_flow(self, odoo_instance):
        self.flow_id.start(odoo_instance)

    def check_incoming_outgoings(self):
        for rec in self:
            if rec.incoming_ids:
                raise ValidationError(("No incoming items allowed for triggers."))
            if rec.outgoing_ids.filtered(lambda x: x.ref._name != "of.start"):
                raise ValidationError(
                    ("Only starts are allowed as trigger destinations.")
                )

    def _start_new_flow_or_continue_existing(self, odoo_instance):
        """
        If next item is start, then a new flow is started;
        If next item is within a flow, flows are continued
        """

        for item in self.outgoing_ids:
            if item.to_id.ref._name == "of.start":
                self._start_new_flow(odoo_instance)
            else:
                for active_trigger in self.env["of.instance.item"].search(
                    [("has_cursor", "=", True), ("item_id", "=", self.item_id.id)]
                ):
                    active_trigger.item_id.ref._continue_in_running_flow(odoo_instance)
