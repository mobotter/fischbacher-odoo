import arrow
import os
import pprint
import logging
import time
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

    def test_simplest(self):
        flow = self.env["of.flow"].create(
            {
                "name": "flow1",
                "model_id": self.env.ref("base.model_res_partner").id,
            }
        )

        name = str(uuid.uuid4())
        partner = self.env["res.partner"].create({"name": name})
        task_item = self.env["of.task"].create(
            {
                "flow_id": flow.id,
                "role_id": self.role.id,
                "name": "rename partner",
                "code": ("obj.name = 'changed'"),
            }
        )
        flow.item_ids[0].outgoing_ids = [
            [
                0,
                0,
                {
                    "to_id": task_item.item_id.id,
                },
            ]
        ]
        task_item.outgoing_ids = [
            [
                0,
                0,
                {"to_id": flow.item_ids.filtered(lambda x: x.ref._name == "of.end").id},
            ]
        ]

        flow_instance = flow.start(partner)
        self.assertEqual(len(flow_instance.item_ids), 1)
        self.assertTrue(flow_instance.item_ids[0].has_cursor)
        self.assertEqual(len(flow.instance_ids), 1)
        flow.heartbeat()
        self.assertEqual(len(flow_instance.item_ids), 2)
        self.assertTrue(not flow_instance.item_ids[0].has_cursor)
        self.assertTrue(flow_instance.item_ids[1].has_cursor)
        flow.heartbeat()
        self.assertEqual(partner.name, "changed")
        self.assertTrue(not flow_instance.active)

    def test_decision(self):
        flow = self.env["of.flow"].create(
            {
                "name": "flow1",
                "model_id": self.env.ref("base.model_res_partner").id,
            }
        )

        partner = self.env["res.partner"].create({"name": name})
        decision = self.env["of.decision"].create(
            {
                "flow_id": flow.id,
                "role_id": self.role.id,
                "name": "decision",
            }
        )
        task_item_should_not = self.env["of.task"].create(
            {
                "flow_id": flow.id,
                "role_id": self.role.id,
                "name": "rename partner1 should not",
                "code": ("obj.name = 'changed'\n" "obj.street = 'should not'\n"),
            }
        )
        task_item_should = self.env["of.task"].create(
            {
                "flow_id": flow.id,
                "role_id": self.role.id,
                "name": "rename partner should be",
                "code": ("obj.name = 'success'"),
            }
        )
        start_item = flow.item_ids[0]
        start_item.outgoing_ids = [[0, 0, {"to_id": decision.item_id.id}]]
        decision.outgoing_ids = [
            [
                0,
                0,
                {
                    "to_id": task_item_should.item_id.id,
                    "condition": f'obj.name == {name}',
                },
            ],
            [
                0,
                0,
                {
                    "to_id": task_item_should_not.item_id.id,
                    "condition": 'obj.name == "rename partner"',
                },
            ],
        ]
        task_item_should_not.outgoing_ids = [
            [
                0,
                0,
                {"to_id": flow.item_ids.filtered(lambda x: x.ref._name == "of.end").id},
            ]
        ]
        task_item_should.outgoing_ids = [
            [
                0,
                0,
                {"to_id": flow.item_ids.filtered(lambda x: x.ref._name == "of.end").id},
            ]
        ]

        flow_instance = flow.start(partner)
        self.assertEqual(len(flow_instance.item_ids), 1)
        self.assertTrue(flow_instance.item_ids[0].has_cursor)
        self.assertEqual(len(flow.instance_ids), 1)
        flow.heartbeat()
        self.assertEqual(len(flow_instance.item_ids), 2)
        self.assertTrue(not flow_instance.item_ids[0].has_cursor)
        self.assertTrue(flow_instance.item_ids[1].has_cursor)
        flow.heartbeat()
        flow.heartbeat()
        self.assertTrue(not flow_instance.active)
        self.assertTrue(not partner.street)
        self.assertEqual(partner.name, "success")

    def test_mail_activity(self):
        flow = self.env["of.flow"].create(
            {
                "name": "flow1",
                "model_id": self.env.ref("base.model_res_partner").id,
            }
        )

        activity_type = self.env["mail.activity.type"].create(
            {
                "name": "type1",
            }
        )

        name = str(uuid.uuid4())
        partner = self.env["res.partner"].create({"name": name})
        mail_activity_item = self.env["of.mail_activity"].create(
            {
                "flow_id": flow.id,
                "role_id": self.role.id,
                "name": "activity 1",
                "activity_type_id": activity_type.id,
                "code": ("obj.name = 'changed'"),
            }
        )
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
        flow.item_ids[0].outgoing_ids = [
            [0, 0, {"to_id": mail_activity_item.item_id.id}]
        ]
        flow.item_ids[0].incoming_ids = [[0, 0, {"from_id": trigger_item.item_id.id}]]
        mail_activity_item.outgoing_ids = [
            [
                0,
                0,
                {"to_id": flow.item_ids.filtered(lambda x: x.ref._name == "of.end").id},
            ]
        ]

        activities = self.env["mail.activity"].search([])
        instances = self.env["of.instance"].search([])
        flow.check_triggers()
        instances2 = self.env["of.instance"].search([])
        flow.check_triggers()
        instances3 = self.env["of.instance"].search([])
        self.assertEqual(len(instances2), len(instances) + 1)
        self.assertEqual(len(instances3), len(instances2))
        flow_instance = instances2 - instances
        flow_instance.heartbeat()  # start --> activity
        flow_instance.heartbeat()  # activiy
        for i in range(100):
            flow_instance.heartbeat()  # activiy
        activities = self.env["mail.activity"].search([]) - activities
        self.assertEqual(len(activities), 1)
        self.assertTrue(flow_instance.active)
        activity = flow_instance.item_ids.filtered(
            lambda x: x.has_cursor
        ).mail_activity_id
        activity.action_done()
        flow_instance.heartbeat()  # activiy
        self.assertFalse(flow_instance.active)
