{
    'name': 'Kombinierter Lieferschein (Auftrag)',
    'version': '19.0.1.0.0',
    'depends': ['base', 'stock', 'sale', 'product', 'l10n_din5008'],
    'author': 'Fischbacher GmbH',
    'license': 'LGPL-3',
    'category': 'stock',
    'summary': 'Kombinierter Lieferschein über alle Lieferungen (erledigt + offen) eines Verkaufsauftrags',
    'data': [
        'report/sale_combined_delivery_template.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'sequence': 110,
}
