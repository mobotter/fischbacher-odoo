# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from pathlib import Path
import json


def migrate(cr, version):
    data = {}
    cr.execute("select id, name, auth_id from zbs_web_url;")
    data["urls"] = cr.fetchall()

    cr.execute(
        "select zbs_web_url_id, zbs_web_proxy_id from zbs_web_proxy_zbs_web_url_rel;"
    )
    data["proxies"] = cr.fetchall()

    Path("/tmp/migweb").write_text(json.dumps(data, indent=2))
