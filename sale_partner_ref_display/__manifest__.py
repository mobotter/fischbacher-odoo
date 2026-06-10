{
    'name': 'Sale Partner Ref Display',
    'version': '19.0.1.0.0',
    'summary': 'Zeigt ref - name (oder id - name) im Kunden-Dropdown des Verkaufsauftrags',
    'description': """
        Erweitert das partner_id-Feld im Verkaufsauftrag (sale.order) so,
        dass der Anzeigename als "ref - name" erscheint.
        Falls keine ref vorhanden ist, wird "id - name" verwendet.
    """,
    'author': 'Moritz Kern',
    'category': 'Sales',
    'depends': ['sale'],
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
