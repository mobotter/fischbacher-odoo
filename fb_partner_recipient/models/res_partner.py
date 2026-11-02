from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    type = fields.Selection(
        selection_add=[("recipient", "Service Recipient")],
        ondelete={"recipient": "set default"},
    )

    @property
    def _complete_name_displayed_types(self):
        """Unterkontakte ohne Namen als 'Firma, Leistungsempfänger' anzeigen."""
        base = getattr(super(), "_complete_name_displayed_types", ("invoice", "delivery", "other"))
        return tuple(base) + ("recipient",)

    def _get_recipient_address(self):
        """Liefert den Leistungsempfänger zum Partner.

        Nutzt die Standard-Logik von address_get(): Unterkontakt mit
        type='recipient', sonst Fallback auf den Kontakt bzw. den Partner selbst.
        """
        self.ensure_one()
        return self.browse(self.address_get(["recipient"])["recipient"])
