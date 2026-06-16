{
    'name': 'Sale Partner Ref Display',
    'version': '19.0.1.0.0',
    'summary': 'Zeigt ref - name bei Kunden und default_code - name bei Produkten in Sales/Subs',
    'description': """
        Erweitert das partner_id-Feld im Verkaufsauftrag (sale.order), so
        dass der Anzeigename als "ref - name" erscheint.
        Falls keine ref vorhanden ist, wird "id - name" verwendet.

        Erweitert außerdem die Produktauswahl in Sales und Subscriptions:
        - Anzeige als "default_code - name"
        - Suche nach default_code und name
        - Blockiert Quick Create aus der Produktsuche
        - Passt die Bezeichnung in Verkaufszeilen an
    """,
    'author': 'Moritz Kern',
    'category': 'Sales',
    'depends': ['sale', 'product', 'sale_subscription'],
    'data': [
        'views/sale_order_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sale_partner_ref_display/static/src/js/partner_ref_widget.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
