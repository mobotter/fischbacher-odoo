{
    "name": "zbsync_transformer_edi",
    "version": "1.0",
    "author": "Zebroo GmbH (hello@zebroo.de)",
    "depends": ["zbsync_mapper"],
    "data": ["security/ir.model.access.csv", "views/zbs_transformer_edi_form.xml"],
    "external_dependencies": {"python": [], "bin": []},
    "assets": {
        "web.assets_backend": ["zbsync_transformer_edi/static/src/css/edi_mapper.css"]
    },
    "demo": [],
    "qweb": [],
    "test": [],
    "application": False,
    "license": "Other proprietary",
}
