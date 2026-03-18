from odoo import api, fields, models, _

class ContactCustom(models.Model):
    _inherit = 'res.partner'

    partner_history_ids = fields.One2many(
        'partner.history.fs', 
        'partner_id', 
        string='Partner History'
    )


class PartnerHistory(models.Model):
    _name = 'partner.history.fs'
    _description = 'Partner History'

    @api.model
    def _get_year_selection(self):
        # Zeitzonen-sicheres Jahr ermitteln
        current = fields.Date.context_today(self).year
        return [(str(y), str(y)) for y in range(1900, current + 1)]

    year = fields.Selection(
        selection=_get_year_selection,
        string='Year',
        # Zeitzonen-sicheres Jahr als Default
        default=lambda self: str(fields.Date.context_today(self).year),
        help="Select the year"
    )
    category_id = fields.Many2one("product.category", string="Categories")
    total_turnover = fields.Float(string="Total Turnover")
    total_margin = fields.Float(string="Total Margin")
    partner_id = fields.Many2one("res.partner", string="Partner")
    note = fields.Char(string="Note")
