{
    'name': 'Sale Partner Ref Display',
    'version': '19.0.1.0.0',
    'summary': 'Zeigt ref - name im Kunden-Dropdown und default_code - name in Auftragspositionen',
    'description': """
        Erweitert das partner_id-Feld im Verkaufsauftrag (sale.order), so
        dass der Anzeigename als "ref - name" erscheint.
        Falls keine ref vorhanden ist, wird "id - name" verwendet.

        Erweitert außerdem die Produktauswahl in Auftragspositionen:
        - Anzeige als "default_code - name"
        - Suche nach default_code und name
        - Ausblenden von "Neu" und "Neu erstellen und bearbeiten"
    """,
    'author': 'Moritz Kern',
    'category': 'Sales',
    'depends': ['sale', 'product'],
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
