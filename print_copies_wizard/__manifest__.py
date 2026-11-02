{
    'name': 'Druck-Kopien für alle Berichte',
    'version': '19.0.2.0.0',
    'category': 'Extra Tools',
    'summary': 'Stellt pro Berichtstyp die Anzahl der IoT-Druckkopien ein.',
    'description': """
        Dieses Modul erweitert ir.actions.report um ein Feld iot_print_copies.
        Beim IoT-Druck wird das generierte Dokument serverseitig entsprechend
        dieser Anzahl vervielfacht und dann an die IoT-Box gesendet.
    """,
    'author': 'Moritz Kern',
    'depends': ['base', 'iot'],
    'data': [
        'views/ir_actions_report_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
