from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_internal_demand = fields.Boolean(
        string="Eigenbedarf",
        default=False,
        copy=False,
        index=True,
        help=(
            "Kennzeichnet den bestehenden Verkaufsbeleg als Eigenbedarf. "
            "Das Kennzeichen ändert keine Preise, Mengen, Positionen, "
            "Berechnungen oder Standardprozesse."
        ),
    )

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)

        if self.env.context.get("default_is_internal_demand"):
            values["is_internal_demand"] = True

        return values

    def action_convert_to_internal_demand(self):
        """Markiert ein Angebot als Eigenbedarf.

        Es wird kein neuer Auftrag erzeugt. Angebotsnummer, Positionen,
        Preise, Mengen, Rabatte, Preisliste, Berechnungen, Chatter, Anhänge
        und der sonstige Standardprozess bleiben unverändert.
        """
        self.ensure_one()

        if self.is_internal_demand:
            raise UserError(
                _("Dieses Angebot ist bereits als Eigenbedarf markiert.")
            )

        if self.state not in ("draft", "sent"):
            raise UserError(
                _(
                    "Nur Angebote im Entwurf oder gesendete Angebote "
                    "können in Eigenbedarf umgewandelt werden."
                )
            )

        self.write({"is_internal_demand": True})

        self.message_post(
            body=_(
                "Der bestehende Beleg wurde als Eigenbedarf markiert. "
                "Preise, Mengen, Positionen und Berechnungen wurden nicht "
                "verändert."
            )
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Eigenbedarf"),
            "res_model": "sale.order",
            "res_id": self.id,
            "view_mode": "form",
            "views": [
                (
                    self.env.ref(
                        "internal_demand.view_order_form_internal_demand"
                    ).id,
                    "form",
                ),
            ],
            "target": "current",
        }

    def action_convert_to_quotation(self):
        """Entfernt ausschließlich das Eigenbedarfs-Kennzeichen."""
        self.ensure_one()

        if not self.is_internal_demand:
            raise UserError(_("Dieser Beleg ist kein Eigenbedarfsbeleg."))

        if self.state not in ("draft", "sent"):
            raise UserError(
                _(
                    "Nur Eigenbedarfsbelege im Entwurf oder gesendete "
                    "Eigenbedarfsbelege können zurück in Angebote "
                    "umgewandelt werden."
                )
            )

        self.write({"is_internal_demand": False})

        self.message_post(
            body=_(
                "Der Eigenbedarfsbeleg wurde zurück in ein normales Angebot "
                "umgewandelt. Preise, Mengen, Positionen und Berechnungen "
                "wurden nicht verändert."
            )
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Angebot"),
            "res_model": "sale.order",
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
        }
