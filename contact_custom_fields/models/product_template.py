from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    use_only_product_pricelist = fields.Boolean(
        string="Nur Produkt-Preisliste verwenden",
        help="Wenn aktiv, werden für Verkaufsauftragszeilen nur produkt- oder variantenbezogene Preislistenregeln berücksichtigt. Globale und Kategorie-Regeln werden ignoriert.",
    )
