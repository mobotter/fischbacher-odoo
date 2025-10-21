# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import os
from pathlib import Path
import os
from odoo.addons.zbsync.tests.test_pipe import ZBSPipelineCase


class SqlTest(ZBSPipelineCase):
    def _get_connection(self):
        conn = self.env["zbs.connection.sql"].create(
            {
                "name": "local",
                "type": "postgres",
                "dbname": self.env.cr.dbname,
                "host": os.getenv("DB_HOST"),
                "port": os.getenv("DB_PORT"),
                "username": os.getenv("DB_USER"),
                "password": os.getenv("DB_PWD"),
            }
        )
        return conn

    def _get_odbc_postgres_connection(self):

        candidates = [
            "/usr/lib/aarch64-linux-gnu/odbc/psqlodbcw.so",
            "/usr/lib/x86_64-linux-gnu/odbc/psqlodbcw.so",
        ]
        for candi in candidates:
            if Path(candi).exists():
                break
        else:
            raise Exception("No odbc lib found.")

        conn = self.env["zbs.connection.sql"].create(
            {
                "name": "localodbc",
                "type": "odbc",
                "connstring": (
                    # "DRIVER={{PostgreSQL Unicode}};"
                    f"DRIVER={{{{{ candi }}}}};"
                    "SERVER={hostname};"
                    "DATABASE={dbname};"
                    "UID={username};"
                    "PWD={password};"
                    "PORT={port};"
                ),
                "dbname": self.env.cr.dbname,
                "host": os.getenv("DB_HOST"),
                "port": os.getenv("DB_PORT"),
                "username": os.getenv("DB_USER"),
                "password": os.getenv("DB_PWD"),
            }
        )
        return conn
