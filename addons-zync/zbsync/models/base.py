# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).

from odoo import api, models


class Base(models.AbstractModel):
    _inherit = "base"

    @api.model
    def zbs_sub_classes(self):
        def collect():
            for name in self.env["zbs.tools"]._get_subclasses(self._name):
                yield self.env[name]

        return list(collect())

    @api.model
    def zbs_sub_classes_for_selection(self):
        def collect():
            for model in self.env["zbs.tools"]._get_subclasses(self._name):
                if (
                    models := self.env["ir.model"]
                    .sudo()
                    .search([("model", "=", model)])
                ):
                    name = models[0].name
                else:
                    name = model

                yield ((model, name))

        return list(collect())

    @api.model
    def inherits_from(self, model):
        if isinstance(model, models.Model):
            model = model._name
        assert isinstance(model, str)
        return model in self.zbs_sub_classes()
