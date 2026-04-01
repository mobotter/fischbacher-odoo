from odoo import api, fields, models
from dateutil.relativedelta import relativedelta


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    purchase_no = fields.Char(string="Purchase")
    order_number = fields.Char(string="Order Number")
    is_rent = fields.Boolean(string="Rent")
    hide_total = fields.Boolean(string="Hide Total Amount")
    german_payment_term = fields.Char(string="Zahlungsbedingungen")
    client_order_name = fields.Text(string="Ordered by")
    client_order_number = fields.Char(string="Your Order Number")

    billing_period_start = fields.Date(compute='_compute_billing_period', store=True)
    billing_period_end = fields.Date(compute='_compute_billing_period', store=True)

    @api.depends()
    def _compute_billing_period(self):
        for order in self:
            next_invoice_date = getattr(order, 'next_invoice_date', False)

            if next_invoice_date:
                order.billing_period_start = next_invoice_date
                order.billing_period_end = next_invoice_date + relativedelta(days=27)
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

        def _get_optional_flag(record):
            for field_name in ('is_optional', 'optional_section'):
                if _field_is_true(record, field_name):
                    return True
            return False

        def _empty_block():
            return {
                'line': False,
                'title': False,
                'is_optional': False,
                'hide_prices': False,
                'hide_composition': False,
                'subtotal': 0.0,
                'product_lines': [],
                'note_lines': [],
            }

        def _make_section(section_line):
            return {
                'line': section_line,
                'title': section_line.name,
                'is_optional': _get_optional_flag(section_line),
                'hide_prices': _field_is_true(section_line, 'hide_price_section'),
                'hide_composition': _field_is_true(section_line, 'hide_composition_section'),
                'subtotal': 0.0,
                'product_lines': [],
                'note_lines': [],
            }

        result = []
        current_block = _empty_block()

        for line in self._get_order_lines_to_report():
            if line.display_type == 'line_section':
                if current_block['title'] or current_block['product_lines'] or current_block['note_lines']:
                    result.append(current_block)
                current_block = _make_section(line)

            elif line.display_type == 'line_note':
                current_block['note_lines'].append(line)

            else:
                current_block['subtotal'] += line.price_subtotal
                current_block['product_lines'].append({
                    'line': line,
                    'show_prices': not current_block['hide_prices'],
                })

        if current_block['title'] or current_block['product_lines'] or current_block['note_lines']:
            result.append(current_block)

        return result
