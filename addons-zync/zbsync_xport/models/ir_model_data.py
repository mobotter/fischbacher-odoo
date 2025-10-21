# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import api, models


class IrModelData(models.Model):
    _inherit = "ir.model.data"

    @api.model
    def _get_upmost_id(self, model, res_id):
        """
        Instead of returning the model xml id for:

        my_special_module.default_product_categ

        return better:
        product.default_product_categ

        Because the later module is more safe in the destination database.
        """
        assert isinstance(model, str)
        data = self.env["ir.model.data"].search(
            [("model", "=", model), ("res_id", "=", res_id)]
        )

        infos = {}

        for row in data:
            infos.setdefault(row.module, {})
            if row.module in ["__export__"]:
                continue
            objmod = self.env["ir.module.module"].search([("name", "=", row.module)])
            if not objmod:
                continue
            infos[row.module]["downstreams"] = list(
                map(
                    lambda x: x.name,
                    objmod[0].downstream_dependencies(exclude_states=("",)),
                )
            )

        # now check if any module is in downstream of another
        for info_module, info in infos.items():
            for info2_module, downstream2 in infos.items():
                if info2_module == info_module:
                    continue
                if info_module in downstream2["downstreams"]:
                    info["child"] = True

        not_children = {k: v for (k, v) in infos.items() if not v.get("child")}
        if not_children:
            # return first parent
            module_name = sorted(list(not_children.keys()))[0]
            data = data.filtered(lambda x: x.module == module_name)[0]
            return data
