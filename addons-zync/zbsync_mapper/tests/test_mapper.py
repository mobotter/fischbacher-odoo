# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
# knowledge-ID: 264
from odoo.addons.zbsync.tests.test_pipe import ZBSPipelineCase
from odoo.tests import tagged
from odoo.addons.zbsync.models.zbs_batch import BatchFailed


@tagged("post_install", "-at_install")
class TestMapper(ZBSPipelineCase):
    _testname = "Mappings"

    def _get_knowledge_base_article_id(self):
        return 264  # "https://www.zebroo.de/knowledge/article/264"

    def _custom_format(self, setup, output):
        def _table_header(output):
            output.append("<tr>")
            output.append(
                """
                <th>Source</th>
                <th>Action</th>
                <th>Destination</th>
                <th>Details</th>
            """
            )
            output.append("</tr>")

        def format_mapping(mapping):
            details = ""
            res = []
            res.append("<tr>")
            res.append(f"   <td>{mapping.get('field_source') or ''}</td>")
            res.append(f"   <td>{mapping.get('action', 'direct')}</td>")
            res.append(f"   <td>{mapping.get('field_dest') or ''}</td>")
            res.append(f"   <td>{details}</td>")
            res.append("</tr>")
            if mapping.get("child_ids"):
                res.append("<tr>")
                res.append("    <td style='min-width: 30px;'></td>")
                res.append("    <td colspan='3'>")
                res.append("        <table border='1'>")
                _table_header(res)
                for child in mapping["child_ids"]:
                    res += format_mapping(child[2])
                res.append("        </table>")
                res.append("    </td>")
                res.append("</tr>")

            return res

        output.append("<h3>Mappings</h3>")
        output.append("<table border='1'>")
        _table_header(output)
        for mapping in setup["mappings"]:
            output += format_mapping(mapping)
        output.append("</table>")

    def test_mappings_simple_direct(self):
        pipe, line = self.make_simple_pipe("zbs.mapper", {})
        mapper = line.worker_id
        setup = {
            "name": "Simple direct mapping",
            "usecase": [],
            "sample_data": {
                "name": "testpartner1",
            },
            "expected_result": [{"firstname": "testpartner1"}],
            "mappings": [
                {
                    "step_id": mapper.id,
                    "field_source": "name",
                    "field_dest": "firstname",
                    "action": "direct",
                    "filter_to_delta": False,
                }
            ],
        }
        data = setup["sample_data"]

        self.env["zbs.mapping"].create(setup["mappings"])

        instance = pipe.start(data)._complete_run()
        data = instance._eval_data()
        self.assertTrue(data._is_equal(setup["expected_result"]))
        self.format_setup(setup)

    def test_hierarchy(self):
        pipe, line = self.make_simple_pipe("zbs.mapper", {})
        mapper = line.worker_id
        setup = {
            "name": "Hierarchical mappings (easy)",
            "sample_data": {
                "name": "testpartner1",
                "street": "strasse1",
            },
            "expected_result": [
                {"firstname": "testpartner1", "address": {"street": "strasse1"}}
            ],
            "mappings": [
                {
                    "step_id": mapper.id,
                    "field_source": "name",
                    "field_dest": "firstname",
                    "action": "direct",
                    "filter_to_delta": False,
                },
                {
                    "step_id": mapper.id,
                    "field_source": "",
                    "field_dest": "address",
                    "action": "object",
                    "filter_to_delta": False,
                    "child_ids": [
                        (
                            0,
                            0,
                            {
                                "field_source": "street",
                                "field_dest": "street",
                                "filter_to_delta": False,
                            },
                        ),
                    ],
                },
            ],
        }

        self.env["zbs.mapping"].create(setup["mappings"])

        instance = pipe.start(setup["sample_data"])._complete_run()
        data = instance._eval_data()
        self.assertTrue(data._is_equal(setup["expected_result"]))
        self.format_setup(setup)

    def test_hierarchy2(self):
        pipe, line = self.make_simple_pipe("zbs.mapper", {})
        mapper = line.worker_id
        setup = {
            "name": "Hierarchical mapping with changing context by diving in",
            "description": """If a field source is given, then the context 'enters' the
                given field and dives into the data-branch""",
            "sample_data": {
                "name": "testpartner1",
                "address": {
                    "street": "strasse1",
                },
            },
            "expected_result": [
                {"firstname": "testpartner1", "address": {"street": "strasse1"}}
            ],
            "mappings": [
                {
                    "step_id": mapper.id,
                    "field_source": "name",
                    "field_dest": "firstname",
                    "action": "direct",
                    "filter_to_delta": False,
                },
                {
                    "step_id": mapper.id,
                    "field_source": "address",
                    "field_dest": "address",
                    "action": "object",
                    "filter_to_delta": False,
                    "child_ids": [
                        (
                            0,
                            0,
                            {
                                "field_source": "street",
                                "field_dest": "street",
                                "filter_to_delta": False,
                                "action": "direct",
                            },
                        ),
                    ],
                },
            ],
        }
        data = setup["sample_data"]

        self.env["zbs.mapping"].create(setup["mappings"])
        instance = pipe.start(data)._complete_run()
        data = instance._eval_data()
        self.assertTrue(data._is_equal(setup["expected_result"]))
        self.format_setup(setup)

    def test_hierarchy3(self):
        pipe, line = self.make_simple_pipe("zbs.mapper", {})
        mapper = line.worker_id
        setup = {
            "sample_data": [[{"created": [[{"id": 313, "name": "partner313"}]]}]],
            "name": "Hierarchy - extract one field from object",
            "mappings": [
                {
                    "step_id": mapper.id,
                    "field_source": "created",
                    "field_dest": "",
                    "action": "object",
                    "filter_to_delta": False,
                    "child_ids": [
                        (
                            0,
                            0,
                            {
                                "field_source": "id",
                                "field_dest": "id",
                                "filter_to_delta": False,
                                "action": "direct",
                            },
                        ),
                    ],
                },
            ],
            "expected_result": [{"id": 313}],
        }
        data = setup["sample_data"]

        self.env["zbs.mapping"].create(setup["mappings"])
        data = pipe.start(data)._complete_run()._eval_data()
        self.assertTrue(data._is_equal(setup["expected_result"]))
        self.format_setup(setup)

    def test_hierarchy4(self):
        pipe, line = self.make_simple_pipe("zbs.mapper", {})
        mapper = line.worker_id
        setup = {
            "name": "Hierarchy extract and combine from different sources",
            "sample_data": {
                "add1": {"street": "street1"},
                "add2": {"street": "street2"},
            },
            "expected_result": [
                {
                    "add1": {"street_mapped": "street1"},
                    "add2": {"street_mapped": "street2"},
                }
            ],
            "mappings": [
                {
                    "step_id": mapper.id,
                    "field_source": "add1",
                    "field_dest": "add1",
                    "action": "object",
                    "child_ids": [
                        (
                            0,
                            0,
                            {
                                "field_source": "street",
                                "field_dest": "street_mapped",
                                "action": "direct",
                            },
                        ),
                    ],
                },
                {
                    "step_id": mapper.id,
                    "field_source": "add2",
                    "field_dest": "add2",
                    "action": "object",
                    "child_ids": [
                        (
                            0,
                            0,
                            {
                                "field_source": "street",
                                "field_dest": "street_mapped",
                                "action": "direct",
                            },
                        ),
                    ],
                },
            ],
        }
        mapper.no_metadata = True
        data = setup["sample_data"]

        self.env["zbs.mapping"].create(setup["mappings"])
        data = pipe.start(data)._complete_run()._eval_data()
        self.assertTrue(data._is_equal(setup["expected_result"]))
        self.format_setup(setup)

    def test_map_odooinstances(self):
        pipe, line = self.make_simple_pipe("zbs.mapper", {})
        mapper = line.worker_id
        setup = {
            "name": "Mapping an odoo instance to json",
            "sample_data": "res.partner name: otto walkes",
            "expected_result": [
                {"firstname": "otto waalkes", "___filter_to_delta": True}
            ],
            "mappings": [
                {
                    "field_source": "name",
                    "field_dest": "firstname",
                    "action": "direct",
                    "step_id": mapper.id,
                    "filter_to_delta": True,
                }
            ],
        }
        partner = self.env["res.partner"].create({"name": "otto waalkes"})

        self.env["zbs.mapping"].create(setup["mappings"])

        instance = pipe.start(partner)._complete_run()
        data = instance._eval_data()
        self.assertTrue(data._is_equal(setup["expected_result"]))
        self.format_setup(setup)

    def test_mapped_values(self):
        pipe, line = self.make_simple_pipe("zbs.mapper", {})
        mapper = line.worker_id
        setup = {
            "expected_result": [{"color_german": "braun"}],
            "sample_data": {
                "name": "testpartner1",
                "color": "brown",
            },
            "mappings": [
                {
                    "step_id": mapper.id,
                    "field_source": "color",
                    "field_dest": "color_german",
                    "action": "mapped_values",
                    "filter_to_delta": False,
                    "mapped_value_ids": [
                        (
                            0,
                            0,
                            {
                                "source_value": "brown",
                                "dest_value": "braun",
                            },
                        )
                    ],
                }
            ],
        }

        data = (setup["sample_data"],)
        self.env["zbs.mapping"].create(setup["mappings"])

        instance = pipe.start(data)._complete_run()
        data = instance._eval_data()
        self.assertTrue(data._is_equal(setup["expected_result"]))
        self.format_setup(setup)

    def test_meta_values(self):
        pipe, line = self.make_simple_pipe("zbs.mapper", {})
        mapper = line.worker_id
        setup = {
            "mappings": [
                {
                    "step_id": mapper.id,
                    "field_source": "name",
                    "field_dest": "firstname",
                    "action": "direct",
                    "is_key": True,
                    "filter_to_delta": False,
                },
                {
                    "step_id": mapper.id,
                    "field_source": "name",
                    "field_dest": "firstname",
                    "action": "direct",
                    "is_key": True,
                    "filter_to_delta": False,
                },
            ],
            "sample_data": {
                "name": "testpartner1",
            },
            "expected_result": [
                {"firstname": "testpartner1", "___keys": ["firstname"]}
            ],
        }
        data = setup["sample_data"]
        self.env["zbs.mapping"].create(setup["mappings"])
        instance = pipe.start(data)._complete_run()
        data = instance._eval_data()
        self.assertTrue(data._is_equal(setup["expected_result"]))
        self.format_setup(setup)

    def test_metadata_may_miss(self):
        pipe, line = self.make_simple_pipe("zbs.mapper", {})
        mapper = line.worker_id
        setup = {
            "mappings": [
                {
                    "step_id": mapper.id,
                    "field_source": "name",
                    "field_dest": "f1",
                    "action": "direct",
                    "filter_to_delta": False,
                },
                {
                    "step_id": mapper.id,
                    "field_source": "name2",
                    "field_dest": "f2",
                    "action": "direct",
                    "may_miss": True,
                    "filter_to_delta": False,
                },
            ],
            "sample_data": [
                {
                    "name": "A",
                },
                {
                    "name": "B",
                    "name2": "C",
                },
            ],
            "expected_result": [{"f1": "A"}, {"f1": "B", "f2": "C"}],
        }

        self.env["zbs.mapping"].create(setup["mappings"])

        instance = pipe.start(setup["sample_data"])._complete_run()
        data = instance._eval_data()
        self.assertTrue(data._is_equal(setup["expected_result"]))

        with self.assertRaises(BatchFailed):
            mapper.root_mapping_ids()[1].may_miss = False
            instance = pipe.start(setup["sample_data"])._complete_run()
            instance._raise_for_status(for_user=True)
        self.format_setup(setup)

    def test_unlink_subrecords(self):
        pipe, line = self.make_simple_pipe("zbs.mapper", {})
        mapper = line.worker_id
        setup = {
            "mappings": [
                {
                    "step_id": mapper.id,
                    "field_source": "name",
                    "field_dest": "f1",
                    "action": "direct",
                    "filter_to_delta": False,
                },
                {
                    "step_id": mapper.id,
                    "field_source": "line_ids",
                    "field_dest": "lines",
                    "action": "direct",
                    "unlink_subrecords": True,
                    "filter_to_delta": False,
                },
            ],
            "sample_data": [
                {"name": "A", "line_ids": [{"product": "A"}]},
            ],
            "expected_result": [
                {"f1": "A", "___keys_delete": ["lines"], "lines": [{"product": "A"}]}
            ],
        }

        self.env["zbs.mapping"].create(setup["mappings"])

        instance = pipe.start(setup["sample_data"])._complete_run()
        data = instance._eval_data()
        expected = setup["expected_result"]
        self.assertTrue(data._is_equal(expected))
        self.format_setup(setup)

    def test_default_value(self):
        pipe, line = self.make_simple_pipe("zbs.mapper", {})
        mapper = line.worker_id
        setup = {
            "mappings": [
                {
                    "step_id": mapper.id,
                    "field_source": "name",
                    "field_dest": "f1",
                    "action": "direct",
                    "default_value": True,
                }
            ],
            "sample_data": [
                {"name": "A", "line_ids": [{"product": "A"}]},
            ],
            "expected_result": [
                {
                    "f1": "A",
                    "___default_values": ["f1"],
                }
            ],
        }

        self.env["zbs.mapping"].create(setup["mappings"])

        instance = pipe.start(setup["sample_data"])._complete_run()
        data = instance._eval_data()
        self.assertTrue(data._is_equal(setup["expected_result"]))
        self.format_setup(setup)

    def test_one2many(self):
        pipe, line = self.make_simple_pipe("zbs.mapper", {})
        mapper = line.worker_id
        setup = {
            "sample_data": [
                {"name": "testpartner1", "field1": "A", "field2": "B"},
            ],
            "expected_result": [
                {
                    "name": "testpartner1",
                    "contacts": [{"product": "A"}, {"product": "B"}],
                }
            ],
            "expected_result1": [
                {
                    "name": "testpartner1",
                    "contacts": [{"product": "B"}, {"product": "A"}],
                }
            ],
            "mappings": [
                {
                    "field_source": "name",
                    "field_dest": "name",
                    "action": "direct",
                },
                {
                    "field_source": "",
                    "field_dest": "contacts",
                    "action": "list",
                    "child_ids": [
                        (
                            0,
                            0,
                            {
                                "field_source": "",
                                "field_dest": "",
                                "action": "object",
                                "child_ids": [
                                    (
                                        0,
                                        0,
                                        {
                                            "field_source": "field1",
                                            "field_dest": "product",
                                            "action": "direct",
                                        },
                                    )
                                ],
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "field_source": "",
                                "field_dest": "",
                                "action": "object",
                                "child_ids": [
                                    (
                                        0,
                                        0,
                                        {
                                            "field_source": "field2",
                                            "field_dest": "product",
                                            "action": "direct",
                                        },
                                    )
                                ],
                            },
                        ),
                    ],
                },
            ],
        }

        self.env["zbs.mapping"].with_context(default_step_id=mapper.id).create(
            setup["mappings"]
        )

        instance = pipe.start(setup["sample_data"])._complete_run()
        data = instance._eval_data()
        self.assertTrue(
            data._is_equal(setup["expected_result"])
            or data._is_equal(setup["expected_result1"])
        )
        self.format_setup(setup)

    def test_many2many_lookup(self):
        country_germany = self.env.ref("base.de")
        country_switzerland = self.env.ref("base.ch")
        setup = {
            "mappings": [
                {
                    "field_source": "name",
                    "field_dest": "name",
                    "action": "direct",
                    "filter_to_delta": False,
                },
                {
                    "field_source": "countries",
                    "field_dest": "marks",
                    "action": "lookup",
                    "filter_to_delta": False,
                    "lookup_model": "res.country",
                    "lookup_field": "name",
                    "format_value": (
                        "list(map(lambda x: x.strip(), value.split(',')))"
                    ),
                },
            ],
            "expected_result": [
                {
                    "name": "testpartner1",
                    "marks": [country_germany.id, country_switzerland.id],
                }
            ],
            "sample_data": [
                {"name": "testpartner1", "countries": "Germany  ,  Switzerland"},
            ],
        }

        pipe, line = self.make_simple_pipe("zbs.mapper", {})
        mapper = line.worker_id
        data = setup["sample_data"]

        self.env["zbs.mapping"].with_context(default_step_id=mapper.id).create(
            setup["mappings"]
        )

        instance = pipe.start(data)._complete_run()
        data = instance._eval_data()
        self.assertTrue(data._is_equal(setup["expected_result"]))
        self.format_setup(setup)

    def test_many2many_from_string(self):
        setup = {
            "sample_data": [
                {"name": "testpartner1", "countries": "Germany  ,  Switzerland"},
            ],
            "mappings": [
                {
                    "field_source": "name",
                    "field_dest": "name",
                    "action": "direct",
                    "filter_to_delta": False,
                },
                {
                    "field_source": "countries",
                    "field_dest": "marks",
                    "action": "list",
                    "filter_to_delta": False,
                    "format_value": (
                        "list(map(lambda x: x.strip(), value.split(',')))"
                    ),
                    "child_ids": [
                        (
                            0,
                            0,
                            {
                                "field_source": "countries",
                                "field_dest": "marks",
                                "action": "list",
                                "filter_to_delta": False,
                                "format_value": (
                                    "list(map(lambda x: x.strip(), value.split(',')))"
                                ),
                            },
                        )
                    ],
                },
            ],
            "expected_result": [
                {
                    "name": "testpartner1",
                    "marks": [country_germany.id, country_switzerland.id],
                }
            ],
        }
        pipe, line = self.make_simple_pipe("zbs.mapper", {})
        mapper = line.worker_id
        data = setup["sample_data"]

        self.env["zbs.mapping"].with_context(default_step_id=mapper.id).create(
            setup["mappings"]
        )

        instance = pipe.start(data)._complete_run()
        data = instance._eval_data()
        country_germany = self.env.ref("base.de")
        country_switzerland = self.env.ref("base.ch")
        self.assertTrue(data._is_equal(setup["expected_result"]))
        self.format_setup(setup)

    def test_many2many_from_string(self):
        setup = {
            "sample_data": [
                {"name": "testpartner1", "countries": "Germany  ,  Switzerland"},
            ],
            "expected_result": [
                {
                    "name": "testpartner1",
                    "marks": [
                        {"code": "GE", "name": "Germany"},
                        {"code": "SW", "name": "Switzerland"},
                    ],
                }
            ],
            "mappings": [
                {
                    "field_source": "name",
                    "field_dest": "name",
                    "action": "direct",
                    "filter_to_delta": False,
                },
                {
                    "field_source": "countries",
                    "field_dest": "marks",
                    "action": "list",
                    "filter_to_delta": False,
                    "format_value": (
                        "list(map(lambda x: x.strip(), value.split(',')))"
                    ),
                    "child_ids": [
                        (
                            0,
                            0,
                            {
                                "field_source": "",
                                "field_dest": "",
                                "action": "object",
                                "filter_to_delta": False,
                                "child_ids": [
                                    (
                                        0,
                                        0,
                                        {
                                            "field_source": "$value",
                                            "field_dest": "name",
                                            "action": "direct",
                                            "filter_to_delta": False,
                                        },
                                    ),
                                    (
                                        0,
                                        0,
                                        {
                                            "field_source": "$value",
                                            "field_dest": "code",
                                            "action": "direct",
                                            "filter_to_delta": False,
                                            "format_value": ("value[:2].upper()"),
                                        },
                                    ),
                                ],
                            },
                        )
                    ],
                },
            ],
        }
        pipe, line = self.make_simple_pipe("zbs.mapper", {})
        mapper = line.worker_id
        data = setup["sample_data"]

        self.env["zbs.mapping"].with_context(default_step_id=mapper.id).create(
            setup["mappings"]
        )

        instance = pipe.start(data)._complete_run()
        data = instance._eval_data()
        if not data._is_equal(setup["expected_result"]):
            raise Exception(data)

        self.assertTrue(data._is_equal(setup["expected_result"]))
        self.format_setup(setup)

    def test_hierarchy_fieldsample(self):
        pipe, line = self.make_simple_pipe("zbs.mapper", {})
        mapper = line.worker_id
        setup = {
            "sample_data": {
                "comment": {
                    "version": 1,
                    "type": "doc",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "besprechung"}],
                        }
                    ],
                }
            },
            "mappings": [
                {
                    "step_id": mapper.id,
                    "action": "direct",
                    "filter_to_delta": False,
                    "field_source": "comment.content.content.text",
                    "field_dest": "text",
                },
            ],
            "expected_result": [{"text": "besprechung"}],
        }

        self.env["zbs.mapping"].create(setup["mappings"])

        instance = pipe.start(setup["sample_data"])._complete_run()
        data = instance._eval_data()
        self.assertTrue(data._is_equal(setup["expected_result"]))
        self.format_setup(setup)

    def test_hierarchy_fieldsample2(self):
        pipe, line = self.make_simple_pipe("zbs.mapper", {})
        mapper = line.worker_id
        setup = {
            "sample_data": {
                "comment": {
                    "version": 1,
                    "type": "doc",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "besprechung"}],
                        }
                    ],
                }
            },
            "expected_result": [{"text": "besprechung"}],
            "mappings": [
                {
                    "step_id": mapper.id,
                    "action": "direct",
                    "filter_to_delta": False,
                    "field_source": "comment.content[0].content[0].text",
                    "field_dest": "text",
                },
            ],
        }

        self.env["zbs.mapping"].create(setup["mappings"])

        instance = pipe.start(setup["sample_data"])._complete_run()
        data = instance._eval_data()
        self.assertTrue(data._is_equal(setup["expected_result"]))
        self.format_setup(setup)

    def test_many2one_lookup_specify_create_values(self):
        setup = {
            "mappings": [
                {
                    "field_source": "main_partner",
                    "field_dest": "mainone",
                    "action": "lookup",
                    "filter_to_delta": False,
                    "lookup_model": "zbs.test.partner",
                    "lookup_field": "name",
                    "child_ids": [
                        [
                            0,
                            0,
                            {
                                "field_source": "'name1'",
                                "field_dest": "name",
                                "action": "eval",
                            },
                        ],
                        [
                            0,
                            0,
                            {
                                "field_source": "'DE'",
                                "field_dest": "country",
                                "action": "eval",
                            },
                        ],
                    ],
                },
            ],
            "sample_data": [
                {"name": "testpartner1", "main_partner": "Germany"},
            ],
            "expected_result": [{"mainone": {"name": "name1", "country": "DE"}}],
        }
        pipe, line = self.make_simple_pipe("zbs.mapper", {})
        mapper = line.worker_id
        mapper.no_metadata = True

        self.env["zbs.mapping"].with_context(default_step_id=mapper.id).create(
            setup["mappings"]
        )

        instance = pipe.start(setup["sample_data"])._complete_run()
        data = instance._eval_data()
        self.assertTrue(data._is_equal(setup["expected_result"]))
        self.format_setup(setup)

    def test_write_to_env(self):
        pipe, line = self.make_simple_pipe("zbs.mapper", {})
        mapper = line.worker_id
        setup = {
            "mappings": [
                {
                    "step_id": mapper.id,
                    "action": "eval",
                    "output_stream": "env",
                    "filter_to_delta": False,
                    "field_source": "comment",
                    "field_dest": "name1",
                    "code": ("instance_env['f1'] = value\n" "value"),
                },
            ],
            "sample_data": [
                {
                    "comment": "HALLO",
                }
            ],
            "expected_result": "HALLO",
        }

        self.env["zbs.mapping"].create(setup["mappings"])

        instance = pipe.start(setup["sample_data"])._complete_run()
        instance_env = instance._get_env()
        self.assertEqual(
            instance_env["f1"],
            setup["expected_result"],
        )
        self.format_setup(setup)

    # TODO
    # def test_skip_record_on_object_or_list(self):
    #     raise NotImplementedError()

    def test_xport(self):
        pipe, line = self.make_simple_pipe("zbs.mapper", {})
        mapper = line.worker_id
        setup = {
            "mappings": {
                "step_id": mapper.id,
                "field_source": "name",
                "field_dest": "firstname",
                "action": "direct",
                "filter_to_delta": False,
            },
            "sample_data": {
                "name": "testpartner1",
            },
        }

        self.env["zbs.mapping"].create(setup["mappings"])

        data = pipe.dump()

        pipe.unlink()
        self.env["zbs.mapping"].search([]).unlink()
        self.assertFalse(self.env["zbs.mapping"].search([]))

        pipe = self.env["zbs.pipeline"].load(data)

        self.assertTrue(self.env["zbs.mapping"].search([]))

    def test_mapping_list_to_list(self):
        setup = {
            "name": "List 2 List",
            "decsription": """
            Basically maps a list to another list.
            """,
            "sample_data": [
                [{"order_lines": [{"name_orderline": "product1"}]}],
            ],
            "expected_result": [
                {
                    "order_lines2": [{"name_dest": "product1"}],
                }
            ],
            "mappings": [
                {
                    "field_source": "order_lines",
                    "field_dest": "order_lines2",
                    "action": "list",
                    "filter_to_delta": False,
                    "child_ids": [
                        (
                            0,
                            0,
                            {
                                "field_source": "",
                                "field_dest": "",
                                "action": "object",
                                "child_ids": [
                                    (
                                        0,
                                        0,
                                        {
                                            "field_source": "name_orderline",
                                            "field_dest": "name_dest",
                                            "action": "direct",
                                            "filter_to_delta": False,
                                        },
                                    )
                                ],
                            },
                        ),
                    ],
                },
            ],
        }
        pipe, line = self.make_simple_pipe("zbs.mapper", {})
        mapper = line.worker_id

        self.env["zbs.mapping"].with_context(default_step_id=mapper.id).create(
            setup["mappings"]
        )

        instance = pipe.start(setup["sample_data"])._complete_run()
        data = instance._eval_data()
        self.assertTrue(data._is_equal(setup["expected_result"]))
        self.format_setup(setup)

    def test_mapping_iterator_start_in_lists(self):
        setup = {
            "name": "Put records into sub-tree as a list",
            "usecase": [
                "Web Api with static header informations",
            ],
            "documentation": """
            Takes a list of records and puts it into chosen places as list again.
            """,
            "sample_data": [{"name": "product 1"}, {"name": "product 2"}],
            "expected_result": [
                {
                    "header_informations": {
                        "version": "1.0",
                    },
                    "products": [
                        {"name": "product 1"},
                        {"name": "product 2"},
                    ],
                }
            ],
            "mappings": [
                {
                    "field_dest": "header_informations",
                    "action": "object",
                    "name": "header",
                    "child_ids": [
                        [
                            0,
                            0,
                            {
                                "field_source": "'1.0'",
                                "field_dest": "version",
                                "action": "eval",
                            },
                        ]
                    ],
                },
                {
                    "field_source": False,
                    "field_dest": "products",
                    "action": "list",
                    "loop_records": True,
                    "filter_to_delta": False,
                    "child_ids": [
                        (
                            0,
                            0,
                            {
                                "field_source": "",
                                "field_dest": "",
                                "action": "object",
                                "name": "product_element",
                                "child_ids": [
                                    (
                                        0,
                                        0,
                                        {
                                            "field_source": "name",
                                            "field_dest": "name",
                                            "action": "direct",
                                        },
                                    )
                                ],
                            },
                        ),
                    ],
                },
            ],
        }

        pipe, line = self.make_simple_pipe("zbs.mapper", {})
        mapper = line.worker_id
        data = setup["sample_data"]

        self.env["zbs.mapping"].with_context(default_step_id=mapper.id).create(
            setup["mappings"]
        )

        instance = pipe.start(data)._complete_run()
        data = instance._eval_data()
        self.assertTrue(data._is_equal(setup["expected_result"]))
        self.format_setup(setup)

    def test_mapping_iterator_start_in_objects(self):
        """ """
        # ------------
        setup = {
            "name": "Put records into sub-tree as object",
            "usecase": [
                "Web Api with static header informations",
            ],
            "documentation": """
            Takes a list of records and selects the last record of it and puts its
            properties into an object.
            """,
            "sample_data": [{"name": "product 1"}, {"name": "product 2"}],
            "expected_result": [
                {
                    "header_informations": {
                        "version": "1.0",
                    },
                    "product": {"name": "product 2"},
                }
            ],
            "mappings": [
                {
                    "field_dest": "header_informations",
                    "action": "object",
                    "name": "header",
                    "child_ids": [
                        [
                            0,
                            0,
                            {
                                "field_source": "'1.0'",
                                "field_dest": "version",
                                "action": "eval",
                            },
                        ]
                    ],
                },
                {
                    "field_source": False,
                    "field_dest": "product",
                    "action": "object",
                    "loop_records": True,
                    "filter_to_delta": False,
                    "child_ids": [
                        (
                            0,
                            0,
                            {
                                "field_source": "name",
                                "field_dest": "name",
                                "action": "direct",
                            },
                        ),
                    ],
                },
            ],
        }
        # ------------

        pipe, line = self.make_simple_pipe("zbs.mapper", {})
        mapper = line.worker_id
        data = setup["sample_data"]

        self.env["zbs.mapping"].with_context(default_step_id=mapper.id).create(
            setup["mappings"]
        )

        instance = pipe.start(data)._complete_run()
        instance._raise_for_status()
        data = instance._eval_data()
        self.assertTrue(data._is_equal(setup["expected_result"]))
        self.format_setup(setup)

    def test_initial_data_access(self):
        pipe, line = self.make_simple_pipe("zbs.mapper", {})
        mapper = line.worker_id
        setup = {
            "name": "How to access initial data",
            "usecase": [],
            "sample_data": {
                "initial_data": {
                    "version": "1.0a",
                }
            },
            "expected_result": [{"v": "1.0a"}],
            "mappings": [
                {
                    "step_id": mapper.id,
                    "field_source": "initial_data.version",
                    "field_dest": "v",
                    "action": "direct",
                }
            ],
        }
        data = setup["sample_data"]

        self.env["zbs.mapping"].create(setup["mappings"])

        instance = pipe.start(data)._complete_run()
        data = instance._eval_data()
        self.assertTrue(data._is_equal(setup["expected_result"]))
        self.format_setup(setup)

    def test_mapping_copy_mappings(self):
        setup = {
            "name": "Tests copying hierarchical mappings",
            "usecase": [
                "Editing pipelines",
            ],
            "documentation": """
            Takes a list of records and puts it into chosen places as list again.
            """,
            "sample_data": [],
            "expected_result": [],
            "mappings": [
                {
                    "field_dest": "object",
                    "action": "object",
                    "name": "header",
                    "child_ids": [
                        [
                            0,
                            0,
                            {
                                "field_source": "1.a",
                                "field_dest": "1.b",
                                "child_ids": [
                                    [
                                        0,
                                        0,
                                        {
                                            "field_source": "1.1.a",
                                            "field_dest": "1.1.b",
                                            "child_ids": [
                                                [
                                                    0,
                                                    0,
                                                    {
                                                        "field_source": "1.1.1.a",
                                                        "field_dest": "1.1.1.b",
                                                    },
                                                ]
                                            ],
                                        },
                                    ]
                                ],
                            },
                        ],
                        [
                            0,
                            0,
                            {
                                "field_source": "1.c",
                                "field_dest": "1.d",
                            },
                        ],
                    ],
                },
            ],
        }

        pipe, line = self.make_simple_pipe("zbs.mapper", {})
        mapper = line.worker_id
        data = setup["sample_data"]

        self.env["zbs.mapping"].with_context(default_step_id=mapper.id).create(
            setup["mappings"]
        )

        mapper = pipe.line_ids.filtered(
            lambda x: x.worker_id._name == "zbs.mapper"
        ).worker_id
        assert len(mapper) == 1

        count = len(self.env["zbs.mapping"].search([]))
        wiz = self.env["zbs.dup.wizard"].create({"src_pipeline_id": pipe.id})
        pipe2 = pipe.browse(wiz.duplicate()["res_id"])
        mapper2 = pipe2.line_ids.filtered(
            lambda x: x.worker_id._name == "zbs.mapper"
        ).worker_id
        assert len(mapper2) == 1

        count2 = len(self.env["zbs.mapping"].search([]))

        assert count2 == 2 * count

        # sorted does not work in V17 - the id is not reprensting the
        # expected order of creation; double checked;
        # but only if the test: test_xport is running before
        mappings1 = mapper.mapping_ids  # .sorted("id")
        mappings2 = mapper2.mapping_ids  # .sorted("id")
        assert len(mappings1) == len(mappings2)
        for i in range(len(mappings1)):
            mapping1 = mappings1[i]
            mapping2 = mappings2.filtered(
                lambda x: x.name.split("#")[1] == mapping1.name.split("#")[1]
            )

            assert len(mapping1.child_ids) == len(mapping2.child_ids)
