{
    "application": False,
    "author": "Zebroo GmbH (hello@zebroo.de)",
    "css": [],
    "data": [
        "views/connection.xml",
        "views/grabber.xml",
        "views/menu.xml",
        "security/ir.model.access.csv",
    ],
    "demo": [],
    "depends": ["zbsync"],
    "external_dependencies": {
        "bin": [],
        "python": ["sqlalchemy", "snowflake-sqlalchemy", "sqlalchemy-utils"],
    },
    "name": "zbsync_snowflake",
    "test": [],
    "version": "1.1",
    "license": "Other proprietary",
    "assets": {"web.assets_qweb": []},
}
