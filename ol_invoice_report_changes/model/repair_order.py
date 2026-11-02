# Author: Moritz Kern
# Company: Fischbacher GmbH + Co. KG

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RepairOrder(models.Model):
    _inherit = "repair.order"

    lease_agreement_no = fields.Char(
        string="DSP-Auftragsnummer",
        copy=False,
        help="Bisherige bzw. externe Auftragsnummer aus DSP3.",
    )

    mk_rental_contract_id = fields.Many2one(
        comodel_name="sale.order",
        string="Auftragsnummer / Mietvertragsnummer",
        domain=lambda self: (
            self.env["sale.order"]._mk_get_rental_contract_domain()
        ),
        check_company=True,
        ondelete="restrict",
        index=True,
        copy=False,
        help=(
            "Zugehörigen Mietpark-Vertrag oder "
            "GEDA-Abonnementvertrag auswählen."
        ),
    )

    @api.constrains("mk_rental_contract_id")
    def _check_mk_rental_contract_id(self):
        """Require a rental or subscription contract when one is selected."""
        for repair in self:
            contract = repair.mk_rental_contract_id

            if contract and not contract._mk_is_rental_contract():
                raise ValidationError(
                    _(
                        "Bitte einen Mietpark-Vertrag oder einen "
                        "GEDA-Abonnementvertrag auswählen."
                    )
                )
