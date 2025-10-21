# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import models


class Mapping(models.Model):
    _inherit = "zbs.mapping"

    def ui_dropped(self, dropped_id):
        dropped_id = int(dropped_id)
        self.ensure_one()
        if not self.parent_id:
            siblings = self.search(
                [("step_id", "=", self.step_id.id), ("parent_id", "=", False)]
            )
        else:
            siblings = self.search([("parent_id", "=", self.parent_id.id)])
        siblings = siblings.sorted()
        # increment afterwards
        passed = False
        dropped = self.browse(dropped_id)
        before, after = self.browse(), self.browse()
        for sibling in siblings:
            if sibling == dropped:
                continue
            if not passed:
                before += sibling
            else:
                after += sibling
            if sibling == self:
                passed = True
        res = {}
        for i, item in enumerate(before + dropped + after, 1):
            item.sequence = i
            res[item.id] = item.sequence
        return res
