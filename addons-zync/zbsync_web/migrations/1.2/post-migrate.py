# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from pathlib import Path
from odoo import api, SUPERUSER_ID
import json


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    zenv = env["zbs.environment"].search([("is_default", "=", True)]).ensure_one()
    data = json.loads(Path("/tmp/migweb").read_text())
    for url in data["urls"]:
        dburl = env["zbs.web.url"].browse(url[0])
        dburl.url_ids.create(
            {
                "name": url[1],
                "auth_id": url[2],
                "url_id": url[0],
                "environment_ids": zenv.ids,
            }
        )

    for proxy in data["proxies"]:
        url_id, proxy_id = proxy
        env["zbs.web.url"].browse(url_id).url_ids.proxy_ids = [[4, proxy_id]]
