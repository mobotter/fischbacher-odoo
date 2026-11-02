# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SaleQuotationLine(models.Model):
    _name = 'sale.quotation.line'
    _description = 'Sale Quotation Line'
    _order = 'sequence, id'

    order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        required=True,
        ondelete='cascade',
    )

    sequence = fields.Integer(
        default=10,
    )

    display_type = fields.Selection(
        selection=[
            ('line_section', 'Section'),
            ('line_note', 'Note'),
        ],
        default=False,
    )

    is_mk_generated = fields.Boolean(
        string='Mietkalkulation-Zeile',
        default=False,
        copy=False,
        readonly=True,
        help=(
            'Kennzeichnet automatisch aus der Mietkalkulation '
            'erzeugte Angebotspositionen.'
        ),
    )

    # Freie sichtbare Produktbezeichnung für Angebotszeilen ohne Eintrag
    # im Odoo-Produktstamm, z. B. "500 Z/ZP".
    quotation_product_name = fields.Char(
        string='Produkt',
        copy=False,
    )

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Produktstamm',
        domain="[('sale_ok', '=', True)]",
        ondelete='restrict',
    )

    product_template_id = fields.Many2one(
        comodel_name='product.template',
        string='Product Template',
        related='product_id.product_tmpl_id',
        depends=['product_id'],
        store=False,
        readonly=True,
    )

    is_configurable_product = fields.Boolean(
        string='Is the product configurable?',
        related='product_template_id.has_configurable_attributes',
        depends=['product_template_id'],
        store=False,
        readonly=True,
    )

    product_type = fields.Selection(
        related='product_id.type',
        string='Product Type',
        depends=['product_id'],
        store=False,
        readonly=True,
    )

    product_uom_qty = fields.Float(
        string='Quantity',
        default=1.0,
    )

    product_uom = fields.Many2one(
        comodel_name='uom.uom',
        string='Unit of Measure',
        compute='_compute_product_uom',
        store=True,
        readonly=False,
        precompute=True,
        ondelete='restrict',
    )

    service_tracking = fields.Selection(
        related='product_template_id.service_tracking',
        string='Service Tracking',
        depends=['product_template_id'],
        store=False,
        readonly=True,
    )

    product_template_attribute_value_ids = fields.Many2many(
        comodel_name='product.template.attribute.value',
        string='Product Template Attribute Values',
        related='product_id.product_template_attribute_value_ids',
        depends=['product_id'],
        store=False,
        readonly=True,
    )

    translated_product_name = fields.Text(
        string='Translated Product Name',
        compute='_compute_translated_product_name',
        readonly=True,
    )

    price_unit = fields.Monetary(
        string='Unit Price',
        currency_field='currency_id',
        default=0.0,
    )

    tax_id = fields.Many2many(
        comodel_name='account.tax',
        string='Taxes',
        compute='_compute_tax_id',
        store=True,
    )

    company_id = fields.Many2one(
        related='order_id.company_id',
        store=True,
        readonly=True,
    )

    currency_id = fields.Many2one(
        related='order_id.currency_id',
        store=True,
        readonly=True,
    )

    price_subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_price_subtotal',
        store=True,
        currency_field='currency_id',
    )

    # Kein Compute-Feld: Die Beschreibung muss bei produktlosen
    # Mietkalkulationspositionen manuell bzw. durch den Generator
    # gesetzt und dauerhaft gespeichert werden.
    name = fields.Text(
        string='Description',
        required=True,
        default='',
    )

    pricelist_item_id = fields.Many2one(
        comodel_name='product.pricelist.item',
        compute='_compute_pricelist_item_id',
    )

    discount = fields.Float(
        string='Discount (%)',
        digits='Discount',
        default=0.0,
    )

    @api.depends('product_id')
    def _compute_product_uom(self):
        unit_uom = self.env.ref(
            'uom.product_uom_unit',
            raise_if_not_found=False,
        )

        for line in self:
            if line.product_id:
                line.product_uom = line.product_id.uom_id
            elif not line.product_uom:
                line.product_uom = unit_uom

    @api.depends(
        'product_id',
        'order_id.partner_id',
        'order_id.partner_id.lang',
    )
    def _compute_translated_product_name(self):
        for line in self:
            if not line.product_id:
                line.translated_product_name = False
                continue

            lang = line.order_id.partner_id.lang or self.env.lang
            product = line.product_id.with_context(lang=lang)
            line.translated_product_name = product.display_name

    @api.onchange(
        'product_id',
        'product_uom',
        'product_uom_qty',
        'order_id',
    )
    def _onchange_product_pricing(self):
        discount_enabled = self.env[
            'product.pricelist.item'
        ]._is_discount_feature_enabled()

        for line in self:
            if not line.product_id or line.display_type:
                continue

            if line.order_id.pricelist_id:
                price = line.order_id.pricelist_id._get_product_price(
                    line.product_id,
                    line.product_uom_qty or 1.0,
                    uom=line.product_uom,
                    date=line.order_id.date_order,
                )
            else:
                price = line.product_id.lst_price

            # Preis nur initial befüllen; manuell gepflegte Preise bleiben.
            if not line.price_unit:
                line.price_unit = price

            # Bei Auswahl eines echten Produkts kann die Bezeichnung
            # automatisch als Produktname übernommen werden.
            if not line.quotation_product_name:
                line.quotation_product_name = line.product_id.display_name

            # Beschreibung nur vorbelegen, wenn noch keine vorhanden ist.
            if not line.name:
                line.name = line.product_id.description or ''

            line._compute_pricelist_item_id()

            if not (
                line.order_id.pricelist_id
                and discount_enabled
                and line.pricelist_item_id
                and line.pricelist_item_id._show_discount()
            ):
                if not line.discount:
                    line.discount = 0.0
                continue

            base_price = line.product_id.lst_price

            if base_price and not line.discount:
                discount = (
                    (base_price - price)
                    / base_price
                    * 100.0
                )

                if (
                    (discount > 0.0 and base_price > 0.0)
                    or (discount < 0.0 and base_price < 0.0)
                ):
                    line.discount = discount
                else:
                    line.discount = 0.0

    @api.depends(
        'product_id',
        'product_id.taxes_id',
        'company_id',
        'order_id.fiscal_position_id',
        'order_id.partner_id',
        'order_id.partner_shipping_id',
    )
    def _compute_tax_id(self):
        for line in self:
            if not line.product_id or line.display_type:
                line.tax_id = False
                continue

            taxes = line.product_id.taxes_id.filtered(
                lambda tax: tax.company_id == line.company_id
            )

            fiscal_position = line.order_id.fiscal_position_id

            line.tax_id = (
                fiscal_position.map_tax(taxes)
                if fiscal_position
                else taxes
            )

    @api.depends(
        'product_id',
        'product_uom',
        'product_uom_qty',
        'order_id.pricelist_id',
        'order_id.date_order',
    )
    def _compute_pricelist_item_id(self):
        for line in self:
            if (
                not line.product_id
                or line.display_type
                or not line.order_id.pricelist_id
            ):
                line.pricelist_item_id = False
                continue

            line.pricelist_item_id = (
                line.order_id.pricelist_id._get_product_rule(
                    line.product_id,
                    quantity=line.product_uom_qty or 1.0,
                    uom=line.product_uom,
                    date=line.order_id.date_order,
                )
            )

    @api.depends(
        'display_type',
        'product_uom_qty',
        'price_unit',
        'discount',
        'tax_id',
        'currency_id',
        'product_id',
        'order_id.partner_id',
        'order_id.partner_shipping_id',
    )
    def _compute_price_subtotal(self):
        for line in self:
            if line.display_type:
                line.price_subtotal = 0.0
                continue

            quantity = line.product_uom_qty or 0.0
            unit_price = line.price_unit or 0.0
            discount = line.discount or 0.0

            price_after_discount = unit_price * (
                1.0 - discount / 100.0
            )

            if line.tax_id:
                taxes = line.tax_id.compute_all(
                    price_after_discount,
                    line.currency_id,
                    quantity,
                    product=line.product_id,
                    partner=(
                        line.order_id.partner_shipping_id
                        or line.order_id.partner_id
                    ),
                )
                line.price_subtotal = taxes['total_excluded']
            else:
                line.price_subtotal = (
                    quantity * price_after_discount
                )
