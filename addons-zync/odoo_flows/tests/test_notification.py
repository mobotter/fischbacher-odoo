import uuid
from datetime import datetime, timedelta
from unittest import skipIf
from odoo import api
from odoo import fields
from odoo.tests import common
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError, RedirectWarning, ValidationError, AccessError


class TestFlow(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.role = self.env["of.role"].create(
            {
                "name": "role1",
            }
        )

    def test_notification(self):
        flow = self.env["of.flow"].create(
            {
                "name": "flow1",
                "model_id": self.env.ref("base.model_res_partner").id,
            }
        )

        recipient1 = self.env["res.partner"].create(
            {
                "name": "recipient1",
            }
        )
        recipient2 = self.env["res.partner"].create(
            {
                "name": "recipient2",
            }
        )
        channel = self.env["mail.channel"].create(
            {
                "name": "channel1",
                "channel_partner_ids": [[4, recipient2.id]],
            }
        )

        user2 = self.env["res.users"].create(
            {
                "name": "user2",
                "login": f"user2-{uuid.uuid4()}-no-notification-please",
            }
        )

        name = str(uuid.uuid4())
        partner = self.env["res.partner"].create(
            {"name": name, "email": "test@test.de"}
        )

        # add follower to see if he gets also notified
        partner.message_follower_ids = [
            [
                0,
                0,
                {
                    "res_model": "res.partner",
                    "res_id": partner.id,
                    "partner_id": user2.partner_id.id,
                    "subtype_ids": self.env["mail.message.subtype"].search([]).ids,
                },
            ]
        ]

        notify_item = self.env["of.notify"].create(
            {
                "flow_id": flow.id,
                "role_id": self.role.id,
                "name": "notify",
                "channel_ids": [[4, channel.id]],
                "partner_ids": [[4, recipient1.id]],
                "wall_type_id": self.env.ref("mail.mt_comment").id,
            }
        )
        notify_item.make_template()
        notify_item.mail_template_id.body_html = "thats from template"
        notify_item.mail_template_id.lang = "en_US"
        notify_item.mail_template_id.partner_to = "${object.id}"

        trigger_item = self.env["of.trigger"].create(
            {
                "flow_id": flow.id,
                "role_id": self.role.id,
                "name": f"find {name}",
                "trigger_by_code": True,
                "code": (
                    "result = env['res.partner']."
                    f"search([('name', '=', '{name}')])"
                ),
            }
        )
        flow.item_ids[0].outgoing_ids = [[0, 0, {"to_id": notify_item.item_id.id}]]
        flow.item_ids[0].incoming_ids = [[0, 0, {"from_id": trigger_item.item_id.id}]]
        notify_item.outgoing_ids = [
            [
                0,
                0,
                {"to_id": flow.item_ids.filtered(lambda x: x.ref._name == "of.end").id},
            ]
        ]

        mails = self.env["mail.mail"].search([])
        instances = self.env["of.instance"].search([])
        flow.check_triggers()
        instances2 = self.env["of.instance"].search([])
        flow.check_triggers()
        instances3 = self.env["of.instance"].search([])
        self.assertEqual(len(instances2), len(instances) + 1)
        self.assertEqual(len(instances3), len(instances2))
        flow_instance = instances2 - instances
        self.assertTrue(flow_instance.active)
        flow_instance.heartbeat()  # start --> notify
        flow_instance.heartbeat()  # notify
        mails = self.env["mail.mail"].search([]) - mails
        self.assertEqual(len(mails), 1)
        self.assertTrue(mails.subject.startswith("Notification:"))

        # make sure it appears as subtype wished on the wall
        message = flow_instance.odoo_instance.message_ids[0]
        self.assertEqual(message, mails.mail_message_id)
        self.assertEqual(message.subtype_id.id, 1)
        self.assertEqual(message.message_type, "comment")  # to be visible on portal
        self.assertEqual(len(mails.recipient_ids), 1)
        self.assertTrue(message.notification_ids)
        self.assertEqual(message.subject, f'Notification: {name} [flow1]')
