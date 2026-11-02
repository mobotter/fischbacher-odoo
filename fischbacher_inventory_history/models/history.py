from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    inventory_history_ids = fields.One2many(
        "product.inventory.history",
        "product_tmpl_id",
        string="Abwertungstabellen",
        copy=False,
    )


class ProductProduct(models.Model):
    _inherit = "product.product"

    variant_inventory_history_ids = fields.One2many(
        "product.inventory.history",
        "product_id",
        string="Abwertungstabellen",
        copy=False,
    )


class ProductInventoryHistory(models.Model):
    _name = "product.inventory.history"
    _description = "Historische Inventur / Abwertungen"
    _order = "date desc, id desc"
    _rec_name = "date"

    product_tmpl_id = fields.Many2one(
        "product.template", string="Produkt",
        required=True, ondelete="cascade", index=True,
    )
    product_id = fields.Many2one(
        "product.product", string="Variante", ondelete="cascade", index=True,
    )
    date = fields.Date(string="Stichtag", required=True, index=True)
    warehouse = fields.Char(string="Lager", required=True)
    quantity = fields.Float(string="Bestand", digits="Product Unit of Measure")
    currency_id = fields.Many2one(
        "res.currency", string="Währung", required=True, readonly=True,
        default=lambda self: self.env.ref("base.EUR"),
    )
    purchase_price = fields.Monetary(string="EK", currency_field="currency_id")
    value = fields.Monetary(
        string="Wert", currency_field="currency_id",
        help="Originalwert; keine automatische Berechnung.",
    )
    base_purchase_price = fields.Monetary(
        string="EK Basis", currency_field="currency_id",
    )
    total_value = fields.Monetary(
        string="Gesamtwert", currency_field="currency_id",
    )
    legacy_article_number = fields.Char(string="Artikelnummer Altsystem")

    # Alte Daten behalten; diese Felder werden nicht mehr importiert/angezeigt.
    additional_quantity = fields.Float(
        string="Bestand (zusätzlich)", digits="Product Unit of Measure",
    )
    legacy_import_key = fields.Char(index=True, copy=False)
    _unique_import_key = models.Constraint(
        "UNIQUE(legacy_import_key)", "Importkennung bereits vorhanden.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            pid = vals.get("product_id") or self.env.context.get("default_product_id")
            if pid and not vals.get("product_tmpl_id"):
                product = self.env["product.product"].browse(pid)
                vals["product_tmpl_id"] = product.product_tmpl_id.id
        return super().create(vals_list)

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id:
            self.product_tmpl_id = self.product_id.product_tmpl_id

    @api.constrains("product_id", "product_tmpl_id", "currency_id")
    def _check_history(self):
        euro = self.env.ref("base.EUR")
        for rec in self:
            if rec.product_id and rec.product_id.product_tmpl_id != rec.product_tmpl_id:
                raise ValidationError("Variante muss zum Produkt gehören.")
            if rec.currency_id != euro:
                raise ValidationError("Historische Beträge müssen in EUR geführt werden.")
