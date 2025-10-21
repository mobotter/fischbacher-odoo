# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo.addons.zbsync.tests.test_pipe import ZBSPipelineCase
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestMapOdooModels(ZBSPipelineCase):
    def test_mappings_simple_direct(self):
        pipe, line = self.make_simple_pipe("zbs.mapper", {})
        mapper = line.worker_id
        data = self.env.user

        self.env["zbs.mapping"].create(
            {
                "step_id": mapper.id,
                "field_source": "name",
                "field_dest": "n1",
                "action": "direct",
                "filter_to_delta": False,
            }
        )
        self.env["zbs.mapping"].create(
            {
                "step_id": mapper.id,
                "field_source": "partner_id.name",
                "field_dest": "partner_name",
                "action": "direct",
                "filter_to_delta": False,
            }
        )

        instance = pipe.start(data)._complete_run()
        data = instance._eval_data()
        self.assertTrue(data._is_equal([{"n1": "OdooBot", "partner_name": "OdooBot"}]))

    def test_skip_record(self):
        pipe, line = self.make_simple_pipe("zbs.mapper", {})
        mapper = line.worker_id
        initial_data = [
            {"name": "A", "line_ids": [{"product": "A"}]},
        ]

        self.env["zbs.mapping"].create(
            {
                "step_id": mapper.id,
                "field_source": "name",
                "field_dest": "f1",
                "action": "direct",
                "default_value": True,
                "skip_record_expr": "value == 'A'",
            },
        )

        instance = pipe.start(initial_data)._complete_run()
        data = instance._eval_data()
        self.assertEqual(data._d, [])

    def test_mappings_m2m_field(self):
        pipe, line = self.make_simple_pipe("zbs.mapper", {})
        mapper = line.worker_id
        order = self.env["zbs.test.order"].create(
            {
                "name": "order1",
                "tag_ids": [
                    [
                        0,
                        0,
                        {
                            "name": "tag1",
                        },
                    ],
                    [
                        0,
                        0,
                        {
                            "name": "tag2",
                        },
                    ],
                ],
            }
        )
        self.env["zbs.mapping"].create(
            {
                "step_id": mapper.id,
                "field_source": "tag_ids",
                "field_dest": "tags",
                "action": "list",
                "filter_to_delta": False,
                "child_ids": [
                    [
                        0,
                        0,
                        {
                            "field_source": "",
                            "field_dest": "",
                            "action": "object",
                            "filter_to_delta": False,
                            "child_ids": [
                                [
                                    0,
                                    0,
                                    {
                                        "field_source": "name",
                                        "field_dest": "n1",
                                        "action": "direct",
                                        "filter_to_delta": False,
                                    },
                                ]
                            ],
                        },
                    ]
                ],
            }
        )

        instance = pipe.start(order)._complete_run()
        data = instance._eval_data()
        self.assertTrue(data._is_equal([{"tags": [{"n1": "tag1"}, {"n1": "tag2"}]}]))
