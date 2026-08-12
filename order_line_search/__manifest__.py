{
    'name': 'Order Line Search',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'author': 'Moritz Kern',
    'maintainer': 'Moritz Kern',
    'website': 'https://github.com/Fischbacher-GmbH-Co-KG/odoo/tree/main/order_line_search',
    'summary': 'Schnelle Suche und Analyse aller Auftragspositionen im Verkaufs-Berichtswesen',
    'depends': [
        'base',
        'sale', 
        'sale_management',
        'sale_stock',!
    ],
    'data': [
        'views/sale_order_line_menu.xml',
        'views/res_partner_views.xml',
        'views/product_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
