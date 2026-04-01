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

        def _get_hide_prices_flag(record):
            for field_name in ('collapse_prices', 'hide_price_section', 'hide_prices'):
                if _field_is_true(record, field_name):
                    return True
            return False

        def _get_hide_composition_flag(record):
            for field_name in ('collapse_composition', 'hide_composition_section', 'hide_composition'):
                if _field_is_true(record, field_name):
                    return True
            return False

        def _new_block(section_line=None):
            return {
                'title': section_line.name if section_line else False,
                'is_optional': _get_optional_flag(section_line) if section_line else False,
                'hide_prices': _get_hide_prices_flag(section_line) if section_line else False,
                'hide_composition': _get_hide_composition_flag(section_line) if section_line else False,
                'subtotal': 0.0,
                'product_lines': [],
                'note_lines': [],
            }

        result = []
        current = _new_block()

        for line in self.order_line.sorted(lambda l: (l.sequence, l.id)):
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

    def _get_report_debug_lines(self):
        self.ensure_one()

        debug_lines = []

        for line in self.order_line.sorted(lambda l: (l.sequence, l.id)):
            interesting_fields = {}

            for fname in sorted(line._fields.keys()):
                low = fname.lower()
                if any(k in low for k in [
                    'hide', 'price', 'compos', 'option', 'section',
                    'display', 'note', 'sequence', 'collapse'
                ]):
                    try:
                        interesting_fields[fname] = line[fname]
                    except Exception as e:
                        interesting_fields[fname] = 'ERROR: %s' % e

            debug_lines.append({
                'id': line.id,
                'sequence': line.sequence,
                'display_type': line.display_type or '',
                'name': line.name or '',
                'qty': getattr(line, 'product_uom_qty', 0.0),
                'price_unit': getattr(line, 'price_unit', 0.0),
                'price_subtotal': getattr(line, 'price_subtotal', 0.0),
                'interesting_fields': interesting_fields,
                'all_field_names': ', '.join(sorted(line._fields.keys())),
            })

        return debug_lines
