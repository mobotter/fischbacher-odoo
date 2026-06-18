{
    'name': 'Partner History',
    'version': '19.0.1.0.0',
    'author': 'Michael Otto',
    'license': 'LGPL-3',
    'category': 'Sales',
    'summary': 'Track partner turnover and margin by year with historical data',
    'description': """
        This module extends Odoo partners (customers/vendors) with comprehensive historical data tracking per year.
        Key Features:
        * Year-by-Year Historical Data: Track partner turnover and margin for each year from 1900 to current
        * Monetary Fields: Properly formatted turnover and margin with currency support (company currency default)
        * Category Filtering: Assign product categories to historical entries for segmented analysis
        * Notes Support: Add custom notes to each historical entry for additional context
        * Inline Editing: Edit partner history directly in the partner form with editable list view
    """,
    'depends': ['base', 'sale'],
    'data': [
        'views/res_partner.xml',
        'security/ir.model.access.csv',
    ],
    'external_dependencies': {"python": [], "bin": []},
    'installable': True,
    'application': False,
    'auto_install': False,
}
