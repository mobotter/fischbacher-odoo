from odoo import fields, models, api
from odoo.tools import html2plaintext

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def get_product_multiline_description_sale(self):
        name = self.display_name

        internal_notes_html = self.description or ''
        if internal_notes_html:
            internal_notes = html2plaintext(internal_notes_html).strip()
            if internal_notes:
                name += '\n' + internal_notes

        return name
