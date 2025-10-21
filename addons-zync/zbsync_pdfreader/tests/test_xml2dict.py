# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo.tests.common import Form
from .common import SqlTest


class SqlGrabber(SqlTest):
    def test_xml2dict(self):
        company = self.env.company
        form = Form(self.env["zbs.pipeline"])
        form.name = "Sql Grabber"
        pipeline = form.save()

        self.add_line(
            pipeline,
            self.env.ref("zbsync_sql.model_zbs_grabber_sql"),
            {
                "sql": (
                    f"select id,name from res_partner where name ilike '{company.name}'"
                ),
                "connection_id": self._get_connection().id,
            },
        )
        instance = pipeline.run_test()._complete_run()

        data = instance._eval_data()
        self.assertEqual(data.name, company.name)

    def test_odbc_postgres(self):
        company = self.env.company
        form = Form(self.env["zbs.pipeline"])
        form.name = "Sql Grabber"
        pipeline = form.save()
        self.add_line(
            pipeline,
            self.env.ref("zbsync_sql.model_zbs_grabber_sql"),
            {
                "sql": (
                    f"select id,name from res_partner where name ilike '{company.name}'"
                ),
                "connection_id": self._get_odbc_postgres_connection().id,
            },
        )
        instance = pipeline.run_test()._complete_run()
        data = instance._eval_data()
        self.assertEqual(data.name, company.name)
