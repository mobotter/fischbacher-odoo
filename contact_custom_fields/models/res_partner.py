from odoo import api, fields, models, _
import calendar

class ContactCustom(models.Model):
    _inherit = 'res.partner'


    telefax = fields.Char("Telefax")
    supplier_customer_number = fields.Char("Supplier Customer Number ")
    dsp3_id = fields.Char("DSP 3 ID")

