
{
    'name': 'partner_history',
    'version': '1.0',
    'author': 'Michael Otto',
    'depends': ['base','sale'],
    'data': [
        'views/res_partner.xml',
        'security/ir.model.access.csv',
    ],
    "external_dependencies": {"python": [], "bin": []},
    #"uninstall_hook": "uninstall_hook",
    #'pre_init_hook': 'pre_init_hook',
    #'post_init_hook': 'post_init_hook',
}
