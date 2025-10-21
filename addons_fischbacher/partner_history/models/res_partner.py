from odoo import api, fields, models, _
import calendar

class ContactCustom(models.Model):
    _inherit = 'res.partner'

    partner_history_ids = fields.One2many('partner.history.fs', 'partner_id')



class PartnerHistory(models.Model):

    _name = 'partner.history.fs'


    @api.model
    def _get_year_selection(self):
        current = fields.datetime.now().year
        return [(str(y), str(y)) for y in range(1900, current + 1)]

    year = fields.Selection(
        selection=_get_year_selection,
        string='Year',
        default=lambda self: str(fields.datetime.now().year),
        help="Select the year"
    )
    category_id = fields.Many2one("product.category","Categories")
    total_turnover = fields.Float("Total Turnover")
    total_margin = fields.Float("Total Margin")
    partner_id = fields.Many2one("res.partner", "Partner")
    note = fields.Char("Note")


