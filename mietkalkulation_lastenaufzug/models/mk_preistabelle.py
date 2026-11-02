# -*- coding: utf-8 -*-

from odoo import fields, models


class MkPreistabelle(models.Model):
    _name = 'mk.preistabelle'
    _description = 'Mietkalkulation Preistabelle'
    _order = 'sequence, name, id'
    _rec_name = 'name'

    sequence = fields.Integer(
        string='Reihenfolge',
        default=10,
    )

    name = fields.Char(
        string='Aufzug',
        required=True,
        index=True,
        help='Kurzbezeichnung der Preiszeile, z. B. „Lastenaufzug 500 kg“.',
    )

    beschreibung = fields.Text(
        string='Beschreibung',
        help='Freier zusätzlicher Beschreibungstext zur Preiszeile.',
    )

    grundpreis = fields.Float(
        string='Grundpreis bis 15 m (€)',
        required=True,
        default=0.0,
    )

    mehrpreis_hoehe = fields.Float(
        string='Mehrpreis je 1,5 m Höhe (€)',
        required=True,
        default=0.0,
    )

    mehrpreis_station = fields.Float(
        string='Mehrpreis je Ladestation (€)',
        required=True,
        default=0.0,
    )

    mehrpreis_buehne_145 = fields.Float(
        string='Mehrpreis Bühne 1,45 × 3,25 m (€)',
        default=0.0,
    )

    mehrpreis_buehne_165 = fields.Float(
        string='Mehrpreis Bühne 1,65 × 4,35 m (€)',
        default=0.0,
    )

    mehrpreis_person = fields.Float(
        string='Mehrpreis Personenbeförderung (€)',
        default=0.0,
    )

    std_je_5m = fields.Float(
        string='Montagestunden je 5 m Höhe',
        default=1.8,
    )

    active = fields.Boolean(
        string='Aktiv',
        default=True,
    )
