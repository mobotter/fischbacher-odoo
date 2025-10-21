# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from oauthlib.oauth2 import (
    BackendApplicationClient,
    MobileApplicationClient,
    LegacyApplicationClient,
)
from requests_oauthlib import OAuth2Session, OAuth1Session


class WebAuth(models.Model):
    _inherit = "zbs.connection.web.auth"

    application_type = fields.Selection(
        [("mobile", "Mobile"), ("backend", "Backend"), ("legacy", "Legacy")]
    )
    client_id = fields.Char("OAuth Client ID", required=False)
    client_secret = fields.Char("OAuth Client Secret", required=False)
    access_token = fields.Char("Oauth Access Token")
    access_secret = fields.Char("Oauth Access Token Secret")
    username = fields.Char("Username")
    password = fields.Char("Password")
    token_url = fields.Char("Token URL", required=False)
    scope = fields.Char(
        "Scope",
        help="https://graph.microsoft.com/.default - may be comma separated",
        required=False,
    )

    auth_type = fields.Selection(
        selection_add=[("oauth2", "OAuth2"), ("oauth1", "OAuth1")],
    )

    @api.constrains("auth_type")
    def _check_required_fields(self):
        for rec in self:
            if rec.auth_type == "oauth2":
                if not rec.client_id or not rec.client_secret:
                    raise ValidationError(
                        "Please provide client-id and client-secret and token-url and a scope."
                    )

    def _oauth2(self, params):
        func = getattr(self, "_" + self.application_type, None)
        oauth, token = func(params)
        params["headers"]["Authorization"] = f'Bearer {token["access_token"]}'
        params["pyrequests"] = oauth

    def _oauth1(self, params):
        oauth = OAuth1Session(
            client_key=self.client_id,
            client_secret=self.client_secret,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_secret,
        )
        params["pyrequests"] = oauth

    def _oauth1(self, params):
        oauth = OAuth1Session(
            client_key=self.client_id,
            client_secret=self.client_secret,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_secret,
        )
        params["pyrequests"] = oauth

    def _backend(self, params):
        scopes = ""
        if self.scope:
            scopes = self.scope.split(",")
        client = BackendApplicationClient(client_id=self.client_id, scope=scopes)
        oauth = OAuth2Session(client=client)
        token = oauth.fetch_token(
            token_url=self.token_url,
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        return oauth, token

    def _legacy(self, params):
        client = LegacyApplicationClient(client_id=self.client_id)
        oauth = OAuth2Session(client=client)
        token = oauth.fetch_token(
            token_url=self.token_url,
            username=self.username,
            password=self.password,
            client_id=self.client_id,
            client_secret=self.client_secret,
            include_client_id=True,
        )
        return oauth, token

    def _mobile(self, params):
        oauth = OAuth2Session(
            client=MobileApplicationClient(client_id=self.client_id), scope=self.scopes
        )
        authorization_url, state = oauth.authorization_url(self.token_url)
        response = oauth.get(authorization_url)
        token = oauth.token_from_fragment(response.url)
        return oauth, token
