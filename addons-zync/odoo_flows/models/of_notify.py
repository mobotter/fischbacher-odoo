from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.tools.safe_eval import safe_eval


class Notify(models.Model):
    _inherits = {"of.base.item": "item_id"}
    _inherit = ["of.base.item.abstract"]
    _name = "of.notify"
    _description = "Flows Notifier"

    include_followers = fields.Boolean("Include Followers (Message Post) of the instance")
    mail_template_id = fields.Many2one(
        "mail.template", string="Template", required=False
    )
    channel_ids = fields.Many2many("discuss.channel", string="Channel")
    partner_ids = fields.Many2many("res.partner", string="Partners")
    user_ids = fields.Many2many("res.users", string="Users")
    wall_type_id = fields.Many2one(
        "mail.message.subtype", string="Subtype", required=False
    )
    body_html = fields.Many2one(
        "ir.ui.view", string="View", domain=[("type", "=", "qweb")]
    )

    def _heartbeat(self, instance_item, additional_data):
        super()._heartbeat(instance_item, additional_data)

        context = {}
        partners = self.partner_ids | self.user_ids.mapped("partner_id")
        context.update(
            dict(
                of_notify_partner_ids=partners.ids,
                flow_user_ids=self.user_ids,
                wk_instance=instance_item.instance_id,
                wk_instance_item=instance_item,
            )
        )

        # if self.include_followers:
        context["include_followers"] = self.include_followers
        if not self.wall_type_id:
            raise ValidationError("Missing walltype id - please configure!")

        instance_item.with_context(context)._odoo_instance.message_post_with_template(
            template_id=self.mail_template_id.id,
            message_type="comment",
            subtype_id=self.wall_type_id.id,
        )
        instance_item._goto_next()

    def make_template(self):
        self.mail_template_id = self.env["mail.template"].create(
            {
                "model_id": self.flow_id.model_id.id,
                "subject": "Notification: {{object.name}} [{{ctx['wk_instance'].flow_id.name}}]",
                "partner_to": "{{ctx['of_notify_partner_ids']}}",
                "auto_delete": False,  # if true, then vanishes also from wall
                "lang": "${object.partner_id.lang}",
            }
        )
