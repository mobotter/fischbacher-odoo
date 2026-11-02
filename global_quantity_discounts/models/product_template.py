# Copyright (c) 2026 Moritz Kern, Fischbacher GmbH + Co. KG
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # Nur auf der Vorlage definiert. `product.product` erbt das Feld über
    # `_inherits`; Varianten und Vorlage haben damit immer denselben Wert.
    discount_allowed = fields.Boolean(
        string="Rabattfähig",
        default=True,
        help=(
            "Wenn deaktiviert, werden prozentuale Rabatte aus der "
            "Kundenpreisliste ignoriert. Festpreise der Kundenpreisliste "
            "gelten weiter und werden mit der globalen Mengenstaffel "
            "verglichen; der günstigere Preis gewinnt."
        ),
    )
