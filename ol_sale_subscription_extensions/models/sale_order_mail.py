from odoo import _, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_quotation_send(self):
        self.ensure_one()

        action = super().action_quotation_send()

        # Individuelle Mietangebote anhand der Mietkalkulation erkennen.
        is_rental_quotation = (
            self.state in ("draft", "sent")
            and bool(self.mk_preistabelle_id)
            and bool(self.quotation_line_ids)
        )

        # Andere Angebote, bestätigte Aufträge und Pro-forma
        # verwenden weiterhin die bisherige Vorlagenauswahl.
        if (
            not is_rental_quotation
            or self.env.context.get("proforma")
        ):
            return action

        template = self.env["mail.template"].browse(71).exists()

        if not template:
            raise UserError(
                _("Die E-Mail-Vorlage mit der ID 71 wurde nicht gefunden.")
            )

        if template.model_id.model != "sale.order":
            raise UserError(
                _(
                    "Die E-Mail-Vorlage mit der ID 71 muss "
                    "für das Modell 'sale.order' eingerichtet sein."
                )
            )

        if not isinstance(action, dict):
            raise UserError(
                _("Der Senden-Button hat keinen gültigen Versanddialog geliefert.")
            )

        action_context = action.get("context") or {}

        if not isinstance(action_context, dict):
            raise UserError(
                _(
                    "Der Senden-Dialog liefert einen unerwarteten Kontext. "
                    "Bitte vorhandene Anpassungen von "
                    "'action_quotation_send' prüfen."
                )
            )

        action["context"] = {
            **action_context,
            "default_template_id": template.id,
        }

        return action
