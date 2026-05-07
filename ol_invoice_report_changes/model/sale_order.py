from odoo import api, fields, models
from dateutil.relativedelta import relativedelta

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    purchase_no = fields.Char(string="Purchase")
    order_number = fields.Char(string="Order Number")
    is_rent = fields.Boolean(string="Rent", compute="_compute_is_rent", store=True)
    hide_total = fields.Boolean(string="Hide Total Amount")
    # german_payment_term = fields.Char(string="Zahlungsbedingungen") <-- WURDE GELÖSCHT
    client_order_name = fields.Text(string="Ordered by")
    client_order_number = fields.Char(string="Your Order Number")

    billing_period_start = fields.Date(compute='_compute_billing_period', store=True)
    billing_period_end = fields.Date(compute='_compute_billing_period', store=True)

    @api.depends('plan_id')
    def _compute_is_rent(self):
        for order in self:
            order.is_rent = bool(order.plan_id)

    @api.depends('next_invoice_date', 'start_date')
    def _compute_billing_period(self):
        for order in self:
            if order.next_invoice_date:
                order.billing_period_end = order.next_invoice_date - relativedelta(days=1)
                order.billing_period_start = order.next_invoice_date - relativedelta(days=28)
            elif hasattr(order, 'start_date') and order.start_date:
                order.billing_period_start = order.start_date
                order.billing_period_end = order.start_date
            else:
                order.billing_period_start = False
                order.billing_period_end = False

    def _find_mail_template(self):
        self.ensure_one()
        if self.env.context.get('proforma'):
            return self.env.ref(
                'ol_invoice_report_changes.email_template_edi_sale_proforma',
                raise_if_not_found=False
            )
        return super()._find_mail_template()

        def _get_report_sections_for_pdf(self):
        self.ensure_one()

        def _field_is_true(record, field_name):
            return bool(record and field_name in record._fields and record[field_name])

        def _new_block(section_line=None):
            return {
                'title': section_line.name if section_line else False,
                'is_optional': _field_is_true(section_line, 'is_optional') if section_line else False,
                'hide_prices': _field_is_true(section_line, 'hide_price_section') if section_line else False,
                'hide_composition': _field_is_true(section_line, 'hide_composition_section') if section_line else False,
                'subtotal': 0.0,
                'product_lines': [],
                'note_lines': [],
            }

        result = []
        current = _new_block()

        # HIER IST DIE WICHTIGE ÄNDERUNG: Wir nutzen is_subscription
        if getattr(self, 'is_subscription', False) and hasattr(self, 'quotation_lines') and self.quotation_lines:
            lines_to_process = self.quotation_lines.sorted(lambda l: (l.sequence, l.id))
        else:
            lines_to_process = self.order_line.sorted(lambda l: (l.sequence, l.id))

        for line in lines_to_process:
            if line.display_type == 'line_section':
                if current['title'] or current['product_lines'] or current['note_lines']:
                    result.append(current)
                current = _new_block(line)
            elif line.display_type == 'line_note':
                current['note_lines'].append(line)
            else:
                line_dict = {
                    'line': line,
                    'show_prices': not current['hide_prices'],
                }
                current['product_lines'].append(line_dict)
                current['subtotal'] += line.price_subtotal

        if current['title'] or current['product_lines'] or current['note_lines']:
            result.append(current)

        return result
