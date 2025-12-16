from odoo import models, fields

# Task ID: 51017
class ContactPerson(models.Model):
    _name = "contact.person"
    _description = "Contact Persons"

    
    salutation = fields.Selection(
        [
            ("mr", "Mr."),
            ("ms", "Ms."),
            ("buchh", "Buchh."),
            ("dr_med", "Dr. med."),
            ("fr", "Fr."),
            ("hr", "Hr"),
            ("heerr", "Heerr"),
            ("vater", "Vater"),
        ],
        string="Salutation",
    )
    first_name = fields.Char(string="First Name")
    last_name = fields.Char(string="Last Name")
    phone_prefix = fields.Char(string="Phone Prefix")
    phone = fields.Char(string="Phone")
    mobile = fields.Char(string="Mobile")
    info = fields.Char(string="Info")
    email = fields.Char(string="Email Address")
    partner_id = fields.Many2one(
        "res.partner",
        string="Contact",
        ondelete="cascade",
        index=True,
    )
# Task ID: 51017