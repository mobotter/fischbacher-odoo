from odoo import fields, models, api
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        domain="[('active', '=', True), ('parent_id', '=', False), ('sale_blocked', '=', False)]",
        required=True,
    )

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Domain für partner_id setzen"""
        logger.warning("=== _onchange_partner_id called ===")
        logger.warning("self: %s", self)
        logger.warning("partner_id: %s", self.partner_id)
        
        domain = [('active', '=', True), ('parent_id', '=', False), ('sale_blocked', '=', False)]
        logger.warning("Setting domain: %s", domain)
        
        return {
            'domain': {
                'partner_id': domain
            }
        }


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _compute_product_id_change(self):
        logger.warning("=== _compute_product_id_change called ===")
        result = super()._compute_product_id_change()
        for line in self:
            if line.product_id:
                product = line.product_id
                code = product.default_code or ''
                name = product.name or ''
                line.name = f"{code} - {name}" if code else name
                logger.warning("Product: %s, Code: %s, Name: %s", product, code, name)
        return result
