# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    for e in env["zbs.grabber.csvexcel"].search([]):
        if e.first_line_headers:
            e.first_line_of_data = 2
        else:
            e.first_line_of_data = 1
            e.data_contains_headers = False
