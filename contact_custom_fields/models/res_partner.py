from odoo import api, fields, models, _

class ContactCustom(models.Model):
    _inherit = 'res.partner'


    x_telefax = fields.Char("Telefax")
    # telefax = fields.Char("Fax")
    supplier_customer_number = fields.Char("Supplier Customer Number ")
    dsp3_id = fields.Char("DSP 3 ID")

