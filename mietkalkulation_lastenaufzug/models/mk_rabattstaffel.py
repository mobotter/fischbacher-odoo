# -*- coding: utf-8 -*-
from odoo import fields, models


class MkRabattstaffel(models.Model):
    _name = 'mk.rabattstaffel'
    _description = 'Mietkalkulation Rabattstaffel'
    _order = 'monate_ab desc, id'

    monate_ab = fields.Float(string='Ab Mietdauer (Monate)', required=True)
    rabatt_prozent = fields.Float(string='Rabatt (%)', required=True)
    active = fields.Boolean(default=True)
