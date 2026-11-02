{
    "name": "Inventur / Abwertungen – Historie und Import",
    "version": "19.0.1.6.0",
    "author": "Moritz Kern",
    "license": "LGPL-3",
    "depends": ["product", "stock_account"],
    "data": [
        "security/ir.model.access.csv",
        "views/history_views.xml",
        "views/import_views.xml",
        "views/product_views.xml",
        "data/cron.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "fischbacher_inventory_history/static/src/xml/valuation_report.xml",
            "fischbacher_inventory_history/static/src/js/valuation_report_sort.js",
        ],
    },
    "installable": True,
    "application": False,
}
