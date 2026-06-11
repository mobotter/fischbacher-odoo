# -*- coding: utf-8 -*-
from odoo import fields, models


class MkPreistabelle(models.Model):
    _name = 'mk.preistabelle'
    _description = 'Mietkalkulation Preistabelle'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    traglast = fields.Selection(
        selection=[
            ('200',  '200 kg'),
            ('300',  '300 kg'),
            ('500',  '500 kg'),
            ('1000', '1000 / 1200 kg'),
            ('1500', '1500 kg'),
            ('2000', '2000 kg'),
        ],
        string='Traglast',
        required=True,
    )
    grundpreis = fields.Float(string='Grundpreis bis 15 m (€)', required=True)
    mehrpreis_hoehe = fields.Float(string='Mehrpreis je 1,5 m Höhe (€)', required=True)
    mehrpreis_station = fields.Float(string='Mehrpreis je Ladestation (€)', required=True)
    mehrpreis_buehne_145 = fields.Float(string='Mehrpreis Bühne 1,45 × 3,25 m (€)')
    mehrpreis_buehne_165 = fields.Float(string='Mehrpreis Bühne 1,65 × 4,35 m (€)')
    mehrpreis_person = fields.Float(string='Mehrpreis Personenbeförderung (€)')
    std_je_5m = fields.Float(string='Montagestunden je 5 m Höhe', default=1.8)
    active = fields.Boolean(default=True)
