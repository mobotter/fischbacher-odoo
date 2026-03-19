# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'DIN 5008 - Sale Fischbacher',
    'version': '19.0.1.0.0',  # Odoo-19-Standard: major.minor.patch.sequence [web:36]
    'summary': 'Anpassung DIN5008-Layout für Fischbacher-Unternehmen',
    'author': 'Odolution',
    'license': 'LGPL-3',
    'category': 'Accounting/Localizations',
    'depends': [
        'l10n_din5008',
    ],
    'data': [
        'report/external_layout_fischbacher.xml',  # Alle Anpassungen hier konsolidiert
    ],
    'auto_install': True,
}
