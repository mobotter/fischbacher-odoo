from odoo import fields , models , api 

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    purchase_no = fields.Char(string="Purchase")
    order_number = fields.Char(string="Order Number")
    is_rent = fields.Boolean(string="Rent")
    hide_total = fields.Boolean(string="Hide Total Amount")
    german_payment_term = fields.Char(string="Zahlungsbedingungen")


    # Task Id 33897 JC
    client_order_name = fields.Text(string="Ordered by")
    client_order_number = fields.Char(string=" Your Order Number")

    def _find_mail_template(self):
        self.ensure_one()

        # ONLY change behavior when proforma button is used
        if self.env.context.get('proforma'):
            return self.env.ref(
                'ol_invoice_report_changes.email_template_edi_sale_proforma',
                raise_if_not_found=False
            )

        # Otherwise keep original logic
        return super()._find_mail_template()

