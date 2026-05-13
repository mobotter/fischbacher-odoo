from odoo import models, fields, api, _
from odoo.tools import html2plaintext
from odoo.exceptions import UserError


class SaleQuotationLine(models.Model):
    _name = 'sale.quotation.line'
    _description = 'Sale Quotation Line'
    _order = 'sequence, id'

    order_id = fields.Many2one('sale.order', string='Sale Order', ondelete='cascade', required=True)
    sequence = fields.Integer(default=10)

    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note"),
    ], default=False)

    product_id = fields.Many2one(
        'product.product',
        string="Product",
        domain="[('sale_ok', '=', True)]",
        ondelete='restrict'
    )

    product_template_id = fields.Many2one(
        'product.template',
        string="Product Template",
        related='product_id.product_tmpl_id',
        depends=['product_id'],
        store=False,
        readonly=True,
    )

    is_configurable_product = fields.Boolean(
        string="Is the product configurable?",
        related='product_template_id.has_configurable_attributes',
        depends=['product_template_id'],
        store=False,
        readonly=True,
    )

    product_type = fields.Selection(
        related='product_id.type',
        string="Product Type",
        depends=['product_id'],
        store=False,
        readonly=True,
    )

    product_uom_qty = fields.Float(string="Quantity", default=1.0)
    product_uom = fields.Many2one(
        'uom.uom',
        string="Unit of Measure",
        compute='_compute_product_uom',
        store=True,
        readonly=False,
        precompute=True,
        ondelete='restrict'
    )

    service_tracking = fields.Selection(
        related='product_template_id.service_tracking',
        string="Service Tracking",
        depends=['product_template_id'],
        store=False,
        readonly=True,
    )

    price_unit = fields.Float(string="Unit Price", digits="Product Price", default=0.0)
    tax_id = fields.Many2many('account.tax', compute='_compute_tax_id', store=True, string='Taxes')
    company_id = fields.Many2one(related='order_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='order_id.currency_id', store=True, readonly=True)
    price_subtotal = fields.Monetary(string="Subtotal", compute='_compute_price_subtotal', store=True)
    name = fields.Text(string="Description", compute='_compute_name', store=True, readonly=False)
    pricelist_item_id = fields.Many2one('product.pricelist.item', compute='_compute_pricelist_item_id')
    discount = fields.Float(string="Discount (%)", digits='Discount', default=0.0)

    @api.depends('product_id')
    def _compute_product_uom(self):
        for line in self:
            if not line.product_uom or (line.product_id and line.product_id.uom_id.id != line.product_uom.id):
                line.product_uom = line.product_id.uom_id

    @api.depends('product_id')
    def _compute_name(self):
        for line in self:
            if not line.product_id:
                if not line.name:
                    line.name = False
                continue
            desc = html2plaintext(line.product_id.description or '').strip()
            line.name = desc

    @api.onchange('product_id', 'product_uom', 'product_uom_qty', 'order_id.pricelist_id')
    def _onchange_product_pricing(self):
        discount_enabled = self.env['product.pricelist.item']._is_discount_feature_enabled()

        for line in self:
            if not line.product_id or line.display_type:
                continue

            if line.order_id.pricelist_id:
                price = line.order_id.pricelist_id._get_product_price(
                    line.product_id,
                    line.product_uom_qty or 1.0,
                    uom=line.product_uom,
                    date=line.order_id.date_order
                )
            else:
                price = line.product_id.lst_price

            if not line.price_unit:
                line.price_unit = price

            line._compute_pricelist_item_id()

            if not (line.order_id.pricelist_id and discount_enabled):
                if not line.discount:
                    line.discount = 0.0
                continue

            if not (line.pricelist_item_id and line.pricelist_item_id._show_discount()):
                if not line.discount:
                    line.discount = 0.0
                continue

            base_price = line.product_id.lst_price
            if base_price and not line.discount:
                discount = (base_price - price) / base_price * 100
                if (discount > 0 and base_price > 0) or (discount < 0 and base_price < 0):
                    line.discount = discount
                else:
                    line.discount = 0.0

    @api.depends('product_id', 'company_id', 'order_id.fiscal_position_id', 'order_id.partner_id', 'order_id.partner_shipping_id')
    def _compute_tax_id(self):
        for line in self:
            if not line.product_id or line.display_type:
                line.tax_id = False
                continue

            taxes = line.product_id.taxes_id.filtered(lambda t: t.company_id == line.company_id)
            fiscal_position = line.order_id.fiscal_position_id

            if fiscal_position:
                line.tax_id = fiscal_position.map_tax(taxes)
            else:
                line.tax_id = taxes

    @api.depends('product_id', 'product_uom', 'product_uom_qty', 'order_id.pricelist_id')
    def _compute_pricelist_item_id(self):
        for line in self:
            if not line.product_id or line.display_type or not line.order_id.pricelist_id:
                line.pricelist_item_id = False
            else:
                line.pricelist_item_id = line.order_id.pricelist_id._get_product_rule(
                    line.product_id,
                    quantity=line.product_uom_qty or 1.0,
                    uom=line.product_uom,
                    date=line.order_id.date_order,
                )

    @api.depends('product_uom_qty', 'price_unit', 'discount', 'tax_id')
    def _compute_price_subtotal(self):
        for line in self:
            if line.display_type:
                line.price_subtotal = 0.0
                continue

            qty = line.product_uom_qty or 0.0
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)

            if line.tax_id:
                taxes = line.tax_id.compute_all(
                    price,
                    line.currency_id,
                    qty,
                    product=line.product_id,
                    partner=line.order_id.partner_shipping_id or line.order_id.partner_id
                )
                line.price_subtotal = taxes['total_excluded']
            else:
                line.price_subtotal = qty * price
