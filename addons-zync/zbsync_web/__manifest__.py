{
    "application": False,
    "author": "Zebroo GmbH (hello@zebroo.de)",
    "data": [
        "views/proxy_tree.xml",
        "views/webviews.xml",
        "views/menu.xml",
        "security/ir.model.access.csv",
    ],
    "demo": [],
    "depends": ["zbsync", "zbsync_receiver"],
    "external_dependencies": {
        "bin": [],
        "python": ["requests", "requests_oauth2client>1.5.0"],
    },
    "name": "zbsync_web",
    "test": [],
    "version": "1.3",
    "assets": {"web.assets_qweb": [], "web.assets_backend": []},
    "license": "Other proprietary",
}
