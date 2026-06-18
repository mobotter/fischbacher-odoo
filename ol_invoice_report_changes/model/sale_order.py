from odoo import api, fields, models
from dateutil.relativedelta import relativedelta


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    purchase_no = fields.Char(
        string="Purchase",
        help="Internal purchase reference or purchase order number.",
    )
    order_number = fields.Char(
        string="Order Number",
        help="Internal order number for this sales order.",
    )

    # Temporäres Kompatibilitätsfeld für alte Views / Studio-Reste
    is_rent = fields.Boolean(string="Rent", compute="_compute_is_rent")
    lease_agreement_no = fields.Char(
        string="Lease Agreement No.",
        copy=False,
        help="Enter the lease agreement number from DSP3 for this rental order.",
    )

    hide_total = fields.Boolean(string="Hide Total Amount")

    client_order_name = fields.Text(
        string="Ordered by",
        help="Name of the person or department who placed this order.",
    )
    client_order_number = fields.Char(
        string="Your Order Number",
        help="The customer's internal order or reference number for this order.",
    )

    billing_period_start = fields.Date(
        string="Billing Period Start",
        compute="_compute_billing_period",
        store=True,
        help="Start date of the current billing period, calculated from the next invoice date.",
    )
    billing_period_end = fields.Date(
        string="Billing Period End",
        compute="_compute_billing_period",
        store=True,
        help="End date of the current billing period, calculated from the next invoice date.",
    )

    @api.depends('plan_id', 'is_subscription')
    def _compute_is_rent(self):
        for order in self:
            order.is_rent = bool(
                ('plan_id' in order._fields and order.plan_id) or
                ('is_subscription' in order._fields and order.is_subscription)
            )

    def _get_billing_timing(self):
        self.ensure_one()
        if (
            'plan_id' in self._fields
            and self.plan_id
            and 'billing_timing' in self.plan_id._fields
            and self.plan_id.billing_timing
        ):
            return self.plan_id.billing_timing
        return 'advance'

    def _calculate_billing_period_dates(self):
        self.ensure_one()

        if not self.next_invoice_date:
            return (False, False)

        billing_timing = self._get_billing_timing()

        if billing_timing == 'arrears':
            billing_end = self.next_invoice_date - relativedelta(days=1)
            billing_start = billing_end - relativedelta(days=27)
        else:
            billing_start = self.next_invoice_date
            billing_end = billing_start + relativedelta(days=27)

        return (billing_start, billing_end)

    @api.depends('next_invoice_date', 'plan_id', 'plan_id.billing_timing')
    def _compute_billing_period(self):
        for order in self:
            billing_start, billing_end = order._calculate_billing_period_dates()
            order.billing_period_start = billing_start
            order.billing_period_end = billing_end

    def _get_billing_period_dates_for_report(self):
        self.ensure_one()
        if self.billing_period_start and self.billing_period_end:
            return (self.billing_period_start, self.billing_period_end)
        return self._calculate_billing_period_dates()

    def _get_billing_period_label_for_report(self):
        self.ensure_one()
        billing_start, billing_end = self._get_billing_period_dates_for_report()
        if not billing_start or not billing_end:
            return False
        return "Billing period from %s to %s" % (
            billing_start.strftime('%d.%m.%Y'),
            billing_end.strftime('%d.%m.%Y'),
        )

    def _prepare_invoice(self):
        self.ensure_one()
        vals = super()._prepare_invoice()

        billing_start, billing_end = self._get_billing_period_dates_for_report()
        vals.update({
            'rental_billing_period_start': billing_start,
            'rental_billing_period_end': billing_end,
            'lease_agreement_no': self.lease_agreement_no,
        })
        return vals

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

        lines_to_process = self.order_line
        is_sub = (
            ('plan_id' in self._fields and self.plan_id) or
            ('is_subscription' in self._fields and self.is_subscription)
        )

        if is_sub:
            if 'quotation_lines' in self._fields and self.quotation_lines:
                lines_to_process = self.quotation_lines
            elif 'quotation_line_ids' in self._fields and self.quotation_line_ids:
                lines_to_process = self.quotation_line_ids

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
