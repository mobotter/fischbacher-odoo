# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).

import os
from odoo import api, SUPERUSER_ID, registry
from odoo.addons.zbsync.tests.test_pipe import ZBSPipelineCase
from contextlib import contextmanager
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class OdooTestCase(ZBSPipelineCase):
    def _get_remote_connection(self):
        return self.env["zbs.connection.odoo"].create(
            {
                "name": "localhost",
                "port": 8069,
                "host": "localhost",
                "dbname": self.env.cr.dbname,
                "username": "admin",
                "password": "admin",
            }
        )

    def _test_connections(self, func, remote=None):
        if not remote:
            conn = self.env.ref("zbsync_odoo.localodoo_connection")
            cr = None
            old_env = self.env
        else:
            cr = registry(self.env.cr.dbname).cursor()
            env = api.Environment(cr, SUPERUSER_ID, {})
            old_env = self.env
            self.env = env
            conn = self._get_remote_connection()
        try:
            func(conn)
        finally:
            if remote:
                cr.rollback()
                cr.close()
            self.env = old_env

    def _preparation_done(self, connection):
        if not connection.is_local_connection:
            self.env.cr.commit()

    def _execute_as_remote(self, connection):
        if not connection.is_local_connection:
            return os.getenv("DEVMODE") == "1"
        else:
            return None
