from odoo import api, fields, models
from dateutil.relativedelta import relativedelta

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    purchase_no = fields.Char(string="Purchase")
    order_number = fields.Char(string="Order Number")
    hide_total = fields.Boolean(string="Hide Total Amount")
    client_order_name = fields.Text(string="Ordered by")
    client_order_number = fields.Char(string="Your Order Number")

    billing_period_start = fields.Date(compute='_compute_billing_period', store=True)
    billing_period_end = fields.Date(compute='_compute_billing_period', store=True)

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

        # Standard-Fallback auf die Verkaufsauftragszeilen
        lines_to_process = self.order_line

        # Nativer Odoo 19 Abo-Check (plan_id oder is_subscription)
        is_sub = getattr(self, 'plan_id', False) or getattr(self, 'is_subscription', False)
        
        if is_sub:
            if 'quotation_lines' in self._fields and getattr(self, 'quotation_lines'):
                lines_to_process = getattr(self, 'quotation_lines')
            elif 'quotation_line_ids' in self._fields and getattr(self, 'quotation_line_ids'):
                lines_to_process = getattr(self, 'quotation_line_ids')

        if 'sequence' in lines_to_process._fields:
            lines_to_process = lines_to_process.sorted(lambda l: (l.sequence, l.id))

        for line in lines_to_process:
            display_type = line.display_type if 'display_type' in line._fields else False

            if display_type == 'line_section':
                if current['title'] or current['product_lines'] or current['note_lines']:
                    result.append(current)
                current = _new_block(line)
            elif display_type == 'line_note':
                current['note_lines'].append(line)
            else:
                line_dict = {
                    'line': line,
                    'show_prices': not current['hide_prices'],
                }
                current['product_lines'].append(line_dict)
                
                if 'price_subtotal' in line._fields:
                    current['subtotal'] += line.price_subtotal
                else:
                    qty = getattr(line, 'product_uom_qty', getattr(line, 'quantity', 0.0))
                    price = getattr(line, 'price_unit', 0.0)
                    current['subtotal'] += (qty * price)

        if current['title'] or current['product_lines'] or current['note_lines']:
            result.append(current)

        return result
