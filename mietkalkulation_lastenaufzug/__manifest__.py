# -*- coding: utf-8 -*-
{
    'name': 'Mietkalkulation Lastenaufzüge / Transportbühnen',
    'version': '19.0.1.13.1',
    'summary': 'Mietkalkulation (pro 4 Wochen) Tab in Abonnement-Aufträgen',
    'description': '''
        Fügt einen "Mietkalkulation"-Tab zum Abonnement-Formular (sale.order) hinzu.
        Berechnet automatisch Mietpreis, Rabatte, Maschinenbruchversicherung
        sowie Montage- und Transportkosten für Lastenaufzüge / Transportbühnen.
    ''',
    'author': 'Moritz Kern',
    'website': 'https://fischbacher.odoo.com',
    'category': 'Sales/Subscriptions',
    'depends': [
        'sale_subscription',
        'ol_sale_subscription_extensions',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/mk_preistabelle_data.xml',
        'data/mk_rabattstaffel_data.xml',
        'views/mk_preistabelle_views.xml',
        'views/mk_rabattstaffel_views.xml',
        'views/sale_order_mietkalkulation_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mietkalkulation_lastenaufzug/static/src/css/mietkalkulation.css',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
