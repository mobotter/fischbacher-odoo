from odoo import api, fields, models, _
import calendar

class ContactCustom(models.Model):
    _inherit = 'res.partner'

    partner_history_ids = fields.One2many('partner.history.fs', 'partner_id')


class PartnerHistory(models.Model):
    _name = 'partner.history.fs'
    _description = 'Partner History' # Gut für Odoo 19, um Warnungen zu vermeiden 

    @api.model
    def _get_year_selection(self):
        # Geändert von fields.datetime zu fields.Datetime
        current = fields.Datetime.now().year
        return [(str(y), str(y)) for y in range(1900, current + 1)]

    year = fields.Selection(
        selection=_get_year_selection,
        string='Year',
        # Geändert von fields.datetime zu fields.Datetime
        default=lambda self: str(fields.Datetime.now().year),
        help="Select the year"
    )
    category_id = fields.Many2one("product.category", "Categories")
    total_turnover = fields.Float("Total Turnover")
    total_margin = fields.Float("Total Margin")
    partner_id = fields.Many2one("res.partner", "Partner")
    note = fields.Char("Note")
