import json
import arrow
from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class InstanceItem(models.Model):
    _name = "of.instance.item"
    _order = "id desc"
    _description = "Flows Instance Item"

    instance_id = fields.Many2one("of.instance")
    item_id = fields.Many2one("of.base.item")
    has_cursor = fields.Boolean("Has Cursor")
    model = fields.Char("Model")
    res_id = fields.Integer("Record ID")
    date_started = fields.Datetime(
        "Date started", default=lambda self: fields.Datetime.now()
    )
    name = fields.Char(compute="_compute_name", store=True)

    mail_activity_id = fields.Many2one("mail.activity", string="mail activity")
    mail_activity_created = fields.Boolean("mail activity was created")
    mail_activity_done = fields.Boolean("mail activity done")

    subflow_instance_id = fields.Many2one("of.instance", "subflow instance")
    subflow_instance_created = fields.Boolean("")
    deadline = fields.Datetime("deadline")

    custom_metadata = fields.Text()

    def store_metadata(self, data):
        data = json.dumps(data, indent=4)
        self.custom_metadata = data

    def restore_metadata(self):
        data = self.custom_metadata or "{}"
        data = json.loads(data)
        return data

    @api.depends("item_id", "item_id.name")
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.item_id.name}"

    @property
    def _odoo_instance(self):
        self.ensure_one()
        return self.env[self.model].sudo().browse(self.res_id)

    def _get_decisions(self):
        raise NotImplementedError()

    def write(self, vals):
        before = dict((x, x.has_cursor) for x in self)
        res = super().write(vals)

        for rec in self:
            if rec.has_cursor != before[rec]:
                rec._on_has_cursor_changed()

        return res

    def _on_has_cursor_changed(self):
        pass

    def _heartbeat(self):
        for rec in self:
            if not rec.has_cursor:
                return
            rec._update_deadline()
            if (
                rec.instance_id.was_started_with_instance
                and (rec._odoo_instance and rec._odoo_instance.exists())
                or not rec.instance_id.was_started_with_instance
            ):
                additional_data = self._fetch_additional_data_for_heartbeat()
                rec.item_id.ref._heartbeat(rec, additional_data=additional_data)
            else:
                rec.instance_id.abort()

    def _update_deadline(self):
        if self.item_id.no_deadline:
            if self.deadline:
                self.deadline = False
        else:
            if not self.deadline:
                deadline = (
                    arrow.utcnow().shift(days=self.item_id.deadline_days).datetime
                )
                self.deadline = fields.Datetime.to_string(deadline)

    @api.model
    def _make_item(self, wk_instance, of_base_item, obj):
        assert of_base_item._name == "of.base.item"
        res = self.create(
            {
                "instance_id": wk_instance.id,
                "item_id": of_base_item.id,
                "model": obj._name if obj else wk_instance.flow_id.model_id.model,
                "res_id": obj.id if obj else False,
            }
        )
        res._update_deadline()
        return res

    @api.model
    def _get_wk_instance_item(self, wk_instance, of_base_item):
        items = self.search(
            [
                ("instance_id", "=", wk_instance.id),
                ("item_id", "=", of_base_item.id),
            ]
        )
        return items

    def _set_cursor(self):
        for rec in self:
            rec.has_cursor = True
            if not rec.date_started:
                rec.date_started = fields.Datetime.now()

    def _goto_next(self, forced=None):
        """
        Item may exist due to another branch going there
        """
        outgoing = self.item_id.outgoing_ids
        needs_check = True
        if forced:
            outgoing = forced
            needs_check = False
        for outgoing in outgoing:
            if not (needs_check and outgoing.applies(self) or not needs_check):
                continue

            item = self._get_wk_instance_item(
                self.instance_id,
                outgoing.to_id,
            )
            if item:
                if item._odoo_instance != self._odoo_instance:
                    raise ValidationError(
                        (
                            "Odoo instances do not match! "
                            f"{item._odoo_instance} vs. {self._odoo_instance}"
                        )
                    )
            else:
                item = self._make_item(
                    self.instance_id, outgoing.to_id, self._odoo_instance
                )
            if item:
                item._set_cursor()
                self.has_cursor = False  # TODO split away?!?
            self.instance_id._compute_is_done()

    def toggle_has_cursor(self):
        self.has_cursor = not self.has_cursor

    @api.constrains("has_cursor")
    def _check_has_cursor(self):
        for rec in self:
            # dont allow no cursor at all
            if not rec.instance_id.item_ids.filtered(lambda x: x.has_cursor):
                raise ValidationError("At least one active item must exist.")

    def open(self):
        return {
            "view_type": "form",
            "res_model": self.item_id.ref._name,
            "res_id": self.item_id.ref.id,
            "views": [(False, "form")],
            "type": "ir.actions.act_window",
            "target": "current",
            "context": {
                "active_model": self._name,
                "active_id": self.id,
            },
        }

    def walk_to_start(self, prev_conn=False):
        for conn, item in self.item_id.walk_to_start(prev_conn=prev_conn):
            yield conn, self._get_wk_instance_item(
                self.instance_id,
                item,
            )

    def _fetch_additional_data_for_heartbeat(self):
        return {}
