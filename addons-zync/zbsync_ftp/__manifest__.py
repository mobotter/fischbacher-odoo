{
    "name": "zbsync_ftp",
    "version": "1.0",
    "author": "Zebroo GmbH (hello@zebroo.de)",
    "depends": ["zbsync_files"],
    "data": [
        "views/connection.xml",
        "views/ftp_dumper.xml",
        "views/ftp_grabber.xml",
        "security/ir.model.access.csv",
    ],
    "external_dependencies": {"python": ["pysftp"], "bin": []},
    "demo": [],
    "qweb": [],
    "test": [],
    "application": False,
    "license": "Other proprietary",
}
