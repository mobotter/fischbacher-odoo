# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MkRabattstaffel(models.Model):
    _name = 'mk.rabattstaffel'
    _description = 'Mietkalkulation Rabattstaffel'
    _order = 'monate_ab desc, id'

    monate_ab = fields.Float(string='Ab Mietdauer (Monate)', required=True)
    rabatt_prozent = fields.Float(string='Rabatt (%)', required=True)
    active = fields.Boolean(default=True)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    mk_basis_hoehe_grundgeraet = fields.Float(
        string='Basis-Höhe inkl. Grundgerät (m)',
        config_parameter='mietkalkulation_lastenaufzug.basis_hoehe_grundgeraet',
        default=15.0,
    )
    mk_schrittweite_mehrhoehe = fields.Float(
        string='Schrittweite Mehrhöhe (m)',
        config_parameter='mietkalkulation_lastenaufzug.schrittweite_mehrhoehe',
        default=1.5,
    )
    mk_maschinenbruch_prozent = fields.Float(
        string='Maschinenbruchversicherung (%)',
        config_parameter='mietkalkulation_lastenaufzug.maschinenbruch_prozent',
        default=4.0,
    )
    mk_rabattstaffel_ids = fields.Many2many(
        'mk.rabattstaffel',
        string='Rabattstaffeln',
        compute='_compute_mk_rabattstaffel_ids',
        inverse='_inverse_mk_rabattstaffel_ids',
    )

    @api.depends_context('uid')
    def _compute_mk_rabattstaffel_ids(self):
        staffeln = self.env['mk.rabattstaffel'].search([], order='monate_ab desc')
        for rec in self:
            rec.mk_rabattstaffel_ids = staffeln

    def _inverse_mk_rabattstaffel_ids(self):
        return True
