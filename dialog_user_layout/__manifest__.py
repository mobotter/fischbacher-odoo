{
    'name': 'Odoo Dialog User Layout',
    'version': '19.0.1.0.3',
    'author': 'Moritz Kern',
    'category': 'Web',
    'summary': 'Draggable and resizable dialogs with per-user saved position and size',
    'depends': ['web'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_users_inherit.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dialog_user_layout/static/src/js/dialog_resizable_draggable.js',
            'dialog_user_layout/static/src/css/dialog_resizable.css',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}
