# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MkKonfiguration(models.Model):
    _name = 'mk.konfiguration'
    _description = 'Mietkalkulation Konfig'

    name = fields.Char(string='Bezeichnung', required=True, default='Standard')
    basis_hoehe_grundgeraet = fields.Float(string='Basis-Höhe inkl. Grundgerät (m)', required=True, default=15.0)
    schrittweite_mehrhoehe = fields.Float(string='Schrittweite Mehrhöhe (m)', required=True, default=1.5)
    maschinenbruch_prozent = fields.Float(string='Maschinenbruchversicherung (%)', required=True, default=4.0)
    active = fields.Boolean(default=True)

    @api.model
    def get_active_config(self):
        return self.search([('active', '=', True)], limit=1) or self.create({'name': 'Standard'})
