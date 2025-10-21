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

    def test_start_by_trigger(self):
        flow = self.env["of.flow"].create(
            {
                "name": "flow1",
                "model_id": self.env.ref("base.model_res_partner").id,
            }
        )

        partner = self.env["res.partner"].create({"name": "versuchskaninchen"})
        task_item = self.env["of.task"].create(
            {
                "flow_id": flow.id,
                "role_id": self.role.id,
                "name": "rename partner",
                "code": ("obj.name = 'changed'"),
            }
        )
        trigger_item = self.env["of.trigger"].create(
            {
                "flow_id": flow.id,
                "role_id": self.role.id,
                "name": "find versuchskaninchen",
                "code": (
                    "result = env['res.partner']."
                    "search([('name', '=', 'versuchskaninchen')])"
                ),
            }
        )
        flow.item_ids[0].outgoing_ids = [[0, 0, {"to_id": task_item.item_id.id}]]
        flow.item_ids[0].incoming_ids = [[0, 0, {"from_id": trigger_item.item_id.id}]]
        task_item.outgoing_ids = [
            [
                0,
                0,
                {"to_id": flow.item_ids.filtered(lambda x: x.ref._name == "of.end").id},
            ]
        ]

        instances = self.env["of.instance"].search([])
        flow.check_triggers()
        instances2 = self.env["of.instance"].search([])
        flow.check_triggers()
        instances3 = self.env["of.instance"].search([])
        self.assertEqual(len(instances2), len(instances) + 1)
        self.assertEqual(len(instances3), len(instances2))

        flow_instance = flow.instance_ids[0]
        self.assertEqual(len(flow_instance.item_ids), 1)
        self.assertTrue(flow_instance.item_ids[0].has_cursor)
        self.assertEqual(len(flow.instance_ids), 1)
        flow.heartbeat()
        self.assertEqual(len(flow_instance.item_ids), 2)
        self.assertTrue(not flow_instance.item_ids[0].has_cursor)
        self.assertTrue(flow_instance.item_ids[1].has_cursor)
        flow.heartbeat()
        self.assertTrue(not flow_instance.active)

    def test_start_by_partner_create(self):
        flow = self.env["of.flow"].create(
            {
                "name": "flow1",
                "model_id": self.env.ref("base.model_res_partner").id,
            }
        )

        task_item = self.env["of.task"].create(
            {
                "flow_id": flow.id,
                "role_id": self.role.id,
                "name": "rename partner",
                "code": ("obj.name = 'changed'"),
            }
        )
        trigger_item = self.env["of.trigger"].create(
            {
                "flow_id": flow.id,
                "role_id": self.role.id,
                "name": "find versuchskaninchen",
                "code": False,
                "trigger_by_create": True,
                "trigger_model_id": self.env.ref("base.model_res_partner").id,
                "trigger_by_create_domain": "[]",
            }
        )
        flow.item_ids[0].outgoing_ids = [[0, 0, {"to_id": task_item.item_id.id}]]
        flow.item_ids[0].incoming_ids = [[0, 0, {"from_id": trigger_item.item_id.id}]]
        task_item.outgoing_ids = [
            [
                0,
                0,
                {"to_id": flow.item_ids.filtered(lambda x: x.ref._name == "of.end").id},
            ]
        ]

        instances = self.env["of.instance"].search([])
        partner = self.env["res.partner"].create({"name": "versuchskaninchen"})
        instances2 = self.env["of.instance"].search([]) - instances
        self.assertEqual(len(instances2), 1)

    def test_start_by_partner_write(self):
        flow = self.env["of.flow"].create(
            {
                "name": "flow1",
                "model_id": self.env.ref("base.model_res_partner").id,
            }
        )

        task_item = self.env["of.task"].create(
            {
                "flow_id": flow.id,
                "role_id": self.role.id,
                "name": "rename partner",
                "code": ("obj.name = 'changed'"),
            }
        )
        street_id = str(uuid.uuid4())
        trigger_item = self.env["of.trigger"].create(
            {
                "flow_id": flow.id,
                "role_id": self.role.id,
                "name": "find versuchskaninchen",
                "code": False,
                "trigger_by_write": True,
                "trigger_model_id": self.env.ref("base.model_res_partner").id,
                "trigger_by_write_domain": f"[('street', '=', '{street_id}')]",
                "trigger_by_write_linkexpression": "env[obj._name].browse(obj.id)",
            }
        )
        flow.item_ids[0].outgoing_ids = [[0, 0, {"to_id": task_item.item_id.id}]]
        flow.item_ids[0].incoming_ids = [[0, 0, {"from_id": trigger_item.item_id.id}]]
        task_item.outgoing_ids = [
            [
                0,
                0,
                {"to_id": flow.item_ids.filtered(lambda x: x.ref._name == "of.end").id},
            ]
        ]

        instances = self.env["of.instance"].search([])
        partner = self.env["res.partner"].create(
            {
                "name": "versuchskaninchen",
                "street": street_id,
            }
        )
        instances2 = self.env["of.instance"].search([]) - instances
        self.assertEqual(len(instances2), 0)

        partner.name = "test123"
        instances3 = self.env["of.instance"].search([]) - instances
        self.assertEqual(len(instances3), 1)

    def test_continue_by_trigger(self):
        flow = self.env["of.flow"].create(
            {
                "name": "flow1",
                "model_id": self.env.ref("base.model_res_partner").id,
            }
        )

        partner = self.env["res.partner"].create({"name": "versuchskaninchen"})
        task1 = self.env["of.task"].create(
            {
                "flow_id": flow.id,
                "role_id": self.role.id,
                "name": "rename partner",
                "code": ("obj.name = '1'"),
            }
        )
        task2 = self.env["of.task"].create(
            {
                "flow_id": flow.id,
                "role_id": self.role.id,
                "name": "rename partner2",
                "code": ("obj.name = '2'"),
            }
        )
        trigger_item = self.env["of.trigger"].create(
            {
                "flow_id": flow.id,
                "role_id": self.role.id,
                "name": "find 1",
                "code": ("result = env['res.partner']." "search([('name', '=', '1')])"),
            }
        )
        flow.item_ids[0].outgoing_ids = [[0, 0, {"to_id": task1.item_id.id}]]
        task1.outgoing_ids = [[0, 0, {"to_id": trigger_item.item_id.id}]]
        trigger_item.outgoing_ids = [
            [
                0,
                0,
                {
                    "to_id": task2.item_id.id,
                },
            ]
        ]
        task2.outgoing_ids = [
            [
                0,
                0,
                {"to_id": flow.item_ids.filtered(lambda x: x.ref._name == "of.end").id},
            ]
        ]

        flow.start(partner)
        flow.heartbeat()  # start --> task1
        flow.heartbeat()  # task1 --> trigger
        self.assertEqual(partner.name, "1")
        flow.check_triggers()  # trigger->task2
        flow.heartbeat()  # trigger continues, because in heartbeat of trigger
        self.assertEqual(partner.name, "2")
        flow.heartbeat()  # task2 --> end

    def test_continue_by_trigger_eventbased(self):
        flow = self.env["of.flow"].create(
            {
                "name": "flow1",
                "model_id": self.env.ref("base.model_res_partner").id,
            }
        )

        street_id = str(uuid.uuid4())
        partner = self.env["res.partner"].create(
            {
                "name": "versuchskaninchen",
                "street": street_id,
            }
        )
        task1 = self.env["of.task"].create(
            {
                "flow_id": flow.id,
                "role_id": self.role.id,
                "name": "rename partner",
                "code": ("obj.name = '1'"),
            }
        )
        task2 = self.env["of.task"].create(
            {
                "flow_id": flow.id,
                "role_id": self.role.id,
                "name": "rename partner2",
                "code": ("obj.name = '2'"),
            }
        )
        trigger_item = self.env["of.trigger"].create(
            {
                "flow_id": flow.id,
                "role_id": self.role.id,
                "name": "find 1",
                "trigger_by_write": True,
                "trigger_model_id": self.env.ref("base.model_res_partner").id,
                "trigger_by_write_domain": f"[('street', '=', '{street_id}')]",
                "trigger_by_write_linkexpression": "env[obj._name].browse(obj.id)",
            }
        )
        flow.item_ids[0].outgoing_ids = [[0, 0, {"to_id": task1.item_id.id}]]
        task1.outgoing_ids = [[0, 0, {"to_id": trigger_item.item_id.id}]]
        trigger_item.outgoing_ids = [
            [
                0,
                0,
                {
                    "to_id": task2.item_id.id,
                },
            ]
        ]
        task2.outgoing_ids = [
            [
                0,
                0,
                {"to_id": flow.item_ids.filtered(lambda x: x.ref._name == "of.end").id},
            ]
        ]

        flow.start(partner)
        flow.heartbeat()  # start --> task1
        flow.heartbeat()  # task1 --> trigger
        self.assertEqual(partner.name, "1")
        partner.name = "3"
        flow.heartbeat()  # trigger continues, because in heartbeat of trigger
        self.assertEqual(partner.name, "2")
        flow.heartbeat()  # task2 --> end
