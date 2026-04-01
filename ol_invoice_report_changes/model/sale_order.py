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

        def _make_section(section_line=None):
            return {
                'line': section_line,
                'title': section_line.name if section_line else False,
                'is_optional': _get_optional_flag(section_line) if section_line else False,
                'hide_prices': _field_is_true(section_line, 'hide_price_section') if section_line else False,
                'hide_composition': _field_is_true(section_line, 'hide_composition_section') if section_line else False,
                'subtotal': 0.0,
                'product_lines': [],
                'note_lines': [],
                'has_any_line': False,
            }

        result = []
        current_section = None
        standalone_lines = []
        standalone_notes = []
        standalone_subtotal = 0.0

        lines = self._get_order_lines_to_report()

        for line in lines:
            if line.display_type == 'line_section':
                if current_section:
                    result.append(current_section)

                if standalone_lines or standalone_notes:
                    result.append({
                        'line': False,
                        'title': False,
                        'is_optional': False,
                        'hide_prices': False,
                        'hide_composition': False,
                        'subtotal': standalone_subtotal,
                        'product_lines': standalone_lines,
                        'note_lines': standalone_notes,
                        'has_any_line': bool(standalone_lines or standalone_notes),
                    })
                    standalone_lines = []
                    standalone_notes = []
                    standalone_subtotal = 0.0

                current_section = _make_section(section_line=line)

            elif line.display_type == 'line_note':
                if current_section:
                    current_section['note_lines'].append(line)
                    current_section['has_any_line'] = True
                else:
                    standalone_notes.append(line)

            else:
                line_dict = {
                    'line': line,
                    'show_prices': not (current_section and current_section['hide_prices']),
                }

                if current_section:
                    current_section['product_lines'].append(line_dict)
                    current_section['subtotal'] += line.price_subtotal
                    current_section['has_any_line'] = True
                else:
                    standalone_lines.append(line_dict)
                    standalone_subtotal += line.price_subtotal

        if current_section:
            result.append(current_section)

        if standalone_lines or standalone_notes:
            result.append({
                'line': False,
                'title': False,
                'is_optional': False,
                'hide_prices': False,
                'hide_composition': False,
                'subtotal': standalone_subtotal,
                'product_lines': standalone_lines,
                'note_lines': standalone_notes,
                'has_any_line': bool(standalone_lines or standalone_notes),
            })

        return result
