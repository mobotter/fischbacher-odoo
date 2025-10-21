# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import yaml
from odoo import models


class Specification(models.Model):
    _inherit = "zbs.api.specification"

    def generate_authorizer(self, start_worker, spec):
        spec = super().generate_authorizer(start_worker, spec)
        data = yaml.safe_load(
            self.env["zbs.receive.authorizer"].search([("name", "=", "JWT")]).api_spec
        )
        res = self.merge(spec, data)
        return res

    def merge(self, a: dict, b: dict, path=[]):
        for key in b:
            if key in a:
                if isinstance(a[key], dict) and isinstance(b[key], dict):
                    self.merge(a[key], b[key], path + [str(key)])
                elif a[key] != b[key]:
                    continue
                    # raise Exception('Conflict at ' + '.'.join(path + [str(key)]))
            else:
                a[key] = b[key]
        return a
