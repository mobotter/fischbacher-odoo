{
    "application": False,
    "author": "Zebroo GmbH (hello@zebroo.de)",
    "css": [],
    "data": [
        "views/backend_model.xml",
        "views/mappings.xml",
        "wizard/create_mapping_wizard.xml",
        "views/menu.xml",
        "security/ir.model.access.csv",
    ],
    "demo": [],
    "depends": ["zbsync", "zbsync_teststruct", "zbsync_xport"],
    "external_dependencies": {"bin": [], "python": ["xmltodict", "pyyaml"]},
    "name": "zbsync_mapper",
    "test": [],
    "version": "1.0",
    "assets": {
        "web.assets_backend": ["zbsync_mapper/static/src/list_renderer.js"],
        "web.assets_qweb": [],
    },
    "license": "Other proprietary",
}
