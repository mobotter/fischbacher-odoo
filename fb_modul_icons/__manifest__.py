{
    'name': 'FB Modul Icons',
    'version': '19.0.1.0.0',
    'summary': 'Überschreibt App-Icons für bestehende Odoo-Module',
    'description': """
        Dieses Modul ersetzt die Standard-App-Icons für Module wie
        Vermietung, Abonnements und weitere, ohne den Odoo-Core zu verändern.
    """,
    'author': 'Fischbacher GmbH + Co. KG',
    'category': 'Customizations',
    'license': 'OPL-1',
    'depends': [
        'base',
        'sale_renting',       # Vermietung
        'sale_subscription',  # Abonnements
    ],
    'assets': {
        'web.assets_backend': [
            'fb_modul_icons/static/src/css/backend_theme.css',
        ],
    },
    'data': [
        'views/menu_icons.xml',
        'views/menu_views.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
