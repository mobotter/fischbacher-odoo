# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import arrow
import json
import base64
from datetime import timedelta
from odoo import api, fields, models

from odoo.addons.zbsync_receiver.exceptions import TokenExpirationException
from odoo.addons.zbsync_receiver.exceptions import TokenInvalidException


class Authorizer(models.Model):
    _inherit = "zbs.receive.authorizer"

    auth_type = fields.Selection(
        selection_add=[("jwt", "JWT")], ondelete={"jwt": "set default"}
    )
    private_key = fields.Text("Private Key")
    pub_key = fields.Text("Public Key")

    def make_rsa_keys(self):
        self.private_key, self.pub_key = self.env["rsa.helper"]._generate_key(4096)

    @api.model
    def _hook_username_password(self, username, password, payload):
        # usually password decryption here
        return username, password

    def authorize_webrequest(self, headers, postdata, keyvalues):
        if self.auth_type == "jwt":
            if headers.get("Authorization"):
                token = (headers["Authorization"] or "").strip().split(" ")
                if len(token) == 2:
                    if token[0].lower() == "bearer":
                        token = token[1].strip()
                        if len(token.split(".")) == 3:
                            token_check = self._check_token(token)
                            return {
                                "authorized": True,
                                "token": token,
                                "payload": token_check["payload"],
                            }

        return super().authorize_webrequest(headers, postdata, keyvalues)

    @api.model
    def _make_token(self, uid, payload):
        assert isinstance(payload, dict)
        HEADER = json.dumps(
            {
                "type": "JWT",
                "alg": "RS256",
                "encoding": "utf8",
            }
        )
        exp_date = (fields.Datetime.now() + timedelta(minutes=60)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        payload.update(
            {
                "odoo_user_id": uid,
                "dbname": self.env.cr.dbname,
                "exp": exp_date,
            }
        )

        PAYLOAD = json.dumps(payload)
        del payload

        HEADER_b64 = self.b64encode(HEADER)
        PAYLOAD_b64 = self.b64encode(PAYLOAD)
        headerstr = HEADER_b64.decode("utf-8")
        payloadstr = PAYLOAD_b64.decode("utf-8")
        SIGNATURE = (f"{headerstr}.{payloadstr}").encode("utf-8")
        SIGNATURE = self.env["rsa.helper"].encrypt(SIGNATURE, self.pub_key)
        SIGNATURE = self.b64encode(SIGNATURE)
        return b".".join([HEADER_b64, PAYLOAD_b64, SIGNATURE]), exp_date

    def b64encode(self, text):
        if isinstance(text, str):
            text = text.encode("utf8")
        text = base64.urlsafe_b64encode(text)
        text = text.rstrip(b"=")
        return text

    def _check_token(self, token):
        HEADER, PAYLOAD, SIGNATURE = token.split(".")
        SIGNATURE = self.env["rsa.helper"].decrypt(
            self.decode(SIGNATURE), self.private_key
        )
        if SIGNATURE != f"{HEADER}.{PAYLOAD}":
            raise TokenInvalidException()
        PAYLOAD = json.loads(base64.urlsafe_b64decode(PAYLOAD + "=="))
        expires = arrow.get(PAYLOAD["exp"])
        if expires < arrow.utcnow():
            raise TokenExpirationException("Token Expired")
        if PAYLOAD["dbname"] != self.env.cr.dbname:
            raise TokenInvalidException("Token Invalid")

        return {"payload": PAYLOAD}

    def _unsalt_password(self, password):
        password = self.decode(password)
        return self.env["rsa.helper"].decrypt(password, self.private_key)

    def decode(self, text):
        text = text.rstrip("==") + "=="
        text = text.encode("utf-8")
        text = base64.urlsafe_b64decode(text)
        return text
