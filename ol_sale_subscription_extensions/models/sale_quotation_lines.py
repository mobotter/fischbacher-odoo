from odoo import models, fields, api
from odoo.tools import html2plaintext

class SaleQuotationLine(models.Model):
    _name = 'sale.quotation.line'
    _description = 'Sale Quotation Line'
    _order = 'sequence, id'

    order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        ondelete='cascade',
        required=True
    )

    sequence = fields.Integer(default=10)

    display_type = fields.Selection(
        [
            ('line_section', "Section"),
            ('line_note', "Note"),
        ],
        default=False
    )

    product_id = fields.Many2one(
        'product.product',
        string="Product",
        domain="[('sale_ok', '=', True)]",
        ondelete='restrict'
    )

    product_uom_qty = fields.Float(
        string="Quantity",
        default=1.0
    )

    product_uom = fields.Many2one(
        comodel_name='uom.uom',
        string="Unit of Measure",
        compute='_compute_product_uom',
        store=True, readonly=False, precompute=True, ondelete='restrict'
    )
    
    price_unit = fields.Float(
        string="Unit Price"
    )

    tax_id = fields.Many2many(
        'account.tax',
        compute='_compute_tax_id',
        store=True,
        string='Taxes'
    )

    company_id = fields.Many2one(
        related='order_id.company_id',
        store=True,
        readonly=True
    )

    currency_id = fields.Many2one(
        related='order_id.currency_id',
        store=True,
        readonly=True
    )

    price_subtotal = fields.Monetary(
        string="Subtotal",
        compute='_compute_price_subtotal',
        store=True
    )
    
    name = fields.Text(
        string="Description",
        compute='_compute_name',
        store=True, readonly=False
    )
    
    pricelist_item_id = fields.Many2one(
        comodel_name='product.pricelist.item',
        compute='_compute_pricelist_item_id'
    )
    
    discount = fields.Float(
        string="Discount (%)",
        compute='_compute_discount',
        digits='Discount',
        store=True, readonly=False, precompute=True)
    
    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_discount(self):
        discount_enabled = self.env['product.pricelist.item']._is_discount_feature_enabled()
        for line in self:
            if not line.product_id or line.display_type:
                line.discount = 0.0

            if not (line.order_id.pricelist_id and discount_enabled):
                continue

            line.discount = 0.0

            if not (line.pricelist_item_id and line.pricelist_item_id._show_discount()):
                # No pricelist rule was found for the product
                # therefore, the pricelist didn't apply any discount/change
                # to the existing sales price.
                continue

            line = line.with_company(line.company_id)
            pricelist_price = line._get_pricelist_price()
            base_price = line._get_pricelist_price_before_discount()

            if base_price != 0:  # Avoid division by zero
                discount = (base_price - pricelist_price) / base_price * 100
                if (discount > 0 and base_price > 0) or (discount < 0 and base_price < 0):
                    # only show negative discounts if price is negative
                    # otherwise it's a surcharge which shouldn't be shown to the customer
                    line.discount = discount

    @api.depends('product_id', 'product_uom', 'product_uom_qty')
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
    
    @api.depends('product_id')
    def _compute_product_uom(self):
        for line in self:
            if not line.product_uom or (line.product_id.uom_id.id != line.product_uom.id):
                line.product_uom = line.product_id.uom_id

    @api.depends('product_id')
    def _compute_name(self):
        for line in self:
            if not line.product_id:
                line.name = False
                # line.description = ''
                continue

            product = line.product_id

            # Start with the base description (or empty string)
            desc = ''

            # Convert HTML description to plain text
            internal_notes_html = product.description or ''
            internal_notes = html2plaintext(internal_notes_html).strip()
            if internal_notes:
                desc += internal_notes  # No need for '\n' if desc is empty

            line.name = desc

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for line in self:
            if not line.product_id:
                continue

            product = line.product_id
            line.price_unit = product.lst_price

            # line.tax_id = product.taxes_id.filtered(
                
            #     lambda t: t.company_id == line.order_id.company_id
            # )
    @api.depends('product_id', 'company_id', 'order_id.fiscal_position_id')
    def _compute_tax_id(self):
        for line in self:
            if not line.product_id:
                line.tax_id = False
                continue

            # 1️⃣ Product taxes filtered by company
            taxes = line.product_id.taxes_id.filtered(
                lambda t: t.company_id == line.company_id
            )

            # 2️⃣ Apply fiscal position (if exists)
            fiscal_position = line.order_id.fiscal_position_id
            if fiscal_position:
                taxes = fiscal_position.map_tax(taxes)

            line.tax_id = taxes

    # @api.depends('product_uom_qty', 'price_unit', 'tax_id')
    # def _compute_price_subtotal(self):
    #     for line in self:
    #         qty = line.product_uom_qty or 0.0
    #         price = line.price_unit or 0.0

    #         # simple subtotal (no tax)
    #         line.price_subtotal = qty * price

    @api.depends('product_uom_qty', 'price_unit', 'discount', 'tax_id')
    def _compute_price_subtotal(self):
        for line in self:
            qty = line.product_uom_qty or 0.0
            price = line.price_unit or 0.0
            discount = line.discount or 0.0

            # Apply discount
            price_after_discount = price * (1 - (discount / 100))

            line.price_subtotal = qty * price_after_discount