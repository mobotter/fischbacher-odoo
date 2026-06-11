# -*- coding: utf-8 -*-
{
    'name': 'Mietkalkulation Lastenaufzüge / Transportbühnen',
    'version': '19.0.1.0.0',
    'summary': 'Mietkalkulation (pro 4 Wochen) Tab in Abonnement-Aufträgen',
    'description': '''
        Fügt einen "Mietkalkulation"-Tab zum Abonnement-Formular (sale.order) hinzu.
        Berechnet automatisch Mietpreis, Rabatte, Maschinenbruchversicherung
        sowie Montage- und Transportkosten für Lastenaufzüge / Transportbühnen.
    ''',
    'author': 'Moritz Kern',
    'website': 'https://fischbacher.odoo.com',
    'category': 'Sales/Subscriptions',
    'depends': ['sale_subscription'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_mietkalkulation_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
