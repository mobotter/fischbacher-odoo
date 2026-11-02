from odoo import models, fields

class StockPickingInherit(models.Model):
    _inherit = 'stock.picking'

    # Wir fügen ein Feld hinzu, das standardmäßig auf 1 steht
    print_copies = fields.Integer(string='Anzahl Druckkopien', default=1, required=True)
