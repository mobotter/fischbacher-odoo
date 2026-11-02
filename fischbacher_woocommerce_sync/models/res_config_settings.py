from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    fischbacher_woo_base_url = fields.Char(
        string="WooCommerce Shop-URL",
        config_parameter="fischbacher_woo.base_url",
        default="https://fischbacher.de",
    )
    fischbacher_woo_consumer_key = fields.Char(
        string="WooCommerce Consumer Key",
        config_parameter="fischbacher_woo.consumer_key",
    )
    fischbacher_woo_consumer_secret = fields.Char(
        string="WooCommerce Consumer Secret",
        config_parameter="fischbacher_woo.consumer_secret",
        password=True,
    )
