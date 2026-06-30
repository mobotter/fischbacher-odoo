{
    'name': 'Odoo Dialog User Layout',
    'version': '19.0.1.0.0',
    'category': 'Web',
    'author': 'Moritz Kern',
    'summary': 'Draggable and resizable dialogs with per-user saved position and size',
    'depends': ['web'],
    'assets': {
        'web.assets_backend': [
            'odoo_dialog_user_layout/static/src/js/dialog_resizable_draggable.js',
            'odoo_dialog_user_layout/static/src/css/dialog_resizable.css',
        ],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/res_users_inherit.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}
