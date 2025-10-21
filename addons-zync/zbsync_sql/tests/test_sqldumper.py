# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import registry
import json
import uuid
from odoo.tests.common import Form
from .common import SqlTest
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class SqlDumper(SqlTest):
    def test_sql_dumper(self):
        form = Form(self.env["zbs.pipeline"])
        form.name = "Sql Dumper"
        pipeline = form.save()
        guid = str(uuid.uuid4())
        const_worker, _ = self.add_line(
            pipeline,
            self.env.ref("zbsync.model_zbs_const"),
            {
                "data": json.dumps(
                    [
                        {
                            "name": guid,
                            "anyfield": "a",
                            "___keys": ["name"],
                        },
                        {
                            "name": guid + "-2",
                            "anyfield": "b",
                            "___keys": ["name"],
                        },
                    ]
                ),
            },
        )

        self.add_line(
            pipeline,
            self.env.ref("zbsync_sql.model_zbs_dumper_sql"),
            {
                "table": "zbs_test_partner",
                "connection_id": self._get_connection().id,
            },
        )
        instance = pipeline.run_test()._complete_run()
        data = instance._eval_data()
        self.assertEqual(data["create"][0]["name"], guid)
        self.assertEqual(data["create"][1]["name"], guid + "-2")

        # update record in sql
        const_worker.data = json.dumps(
            [
                {
                    "name": guid,
                    "anyfield": "aa",
                    "___keys": ["name"],
                },
                {
                    "name": guid + "-2",
                    "anyfield": "bb",
                    "___keys": ["name"],
                },
            ]
        )

        instance = pipeline.run_test()._complete_run()
        data = instance._eval_data()
        self.assertEqual(data["update"][0]["name"], guid)
        self.assertEqual(data["update"][1]["name"], guid + "-2")

        cr2 = registry(self.env.cr.dbname).cursor()
        cr2.execute("select anyfield from zbs_test_partner where name = %s", (guid,))
        self.assertEqual(cr2.fetchone()[0], "aa")
