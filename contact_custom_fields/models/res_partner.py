from odoo import api, fields, models, _

class ContactCustom(models.Model):
    _inherit = 'res.partner'

    steuer_id = fields.Char(
        string="Steuer-Identifikationsnummer",
        help=" Die elfstellige, lebenslang gültige Nummer für Privatpersonen. Sie wird vom Bundeszentralamt für Steuern vergeben."
    )
    steuer_nr = fields.Char(
        string="Steuernummer",
        help="Die individuelle, 10- bis 13-stellige Nummer vom lokalen Finanzamt, die sich bei Wohnortwechseln ändern kann."
    )
    x_telefax = fields.Char(
        string="Telefax",
        help="Faxnummer des Kontakts."
    )
    supplier_customer_number = fields.Char(
        string="Supplier Customer Number",
        help="Kundennummer, unter der wir beim Lieferanten geführt werden."
    )
    dsp3_id = fields.Char(
        string="DSP 3 ID",
        help="Interne oder externe DSP-3-Referenznummer."
    )
