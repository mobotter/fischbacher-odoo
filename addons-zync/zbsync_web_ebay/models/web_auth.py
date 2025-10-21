# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import urllib
import time
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from . import util, oauthmodel
from werkzeug.urls import url_encode, url_decode
import requests
import json
from datetime import datetime, timedelta
from selenium import webdriver
import re


class WebAuth(models.Model):
    _inherit = "zbs.connection.web.auth"

    auth_type = fields.Selection(
        selection_add=[("ebay", "Ebay"), ("ebay_auth_grant", "Ebay Auth Grant")],
    )

    ebay_env = fields.Selection(
        [("environment.PRODUCTION", "Production"), ("environment.SANDBOX", "Sandbox")]
    )
    ebay_user_id = fields.Char("Ebay User ID")
    ebay_user_pw = fields.Char("Ebay User PW")
    ebay_auth_url = fields.Char("Ebay Auth Url")
    ebay_auth_code = fields.Char("Ebay Auth Code")

    @api.constrains("auth_type")
    def _check_required_fields(self):
        for rec in self:
            super()._check_required_fields()
            if rec.auth_type == "ebay":
                if not rec.client_id or not rec.client_secret:
                    raise ValidationError(
                        "Please provide client-id and client-secret and token-url and a scope."
                    )

    def _ebay(self, params):
        func = getattr(self, "_backend", None)
        oauth, token = func(params)
        params["headers"]["Authorization"] = f'Bearer {token["access_token"]}'

    def _ebay_auth_grant(self, params):
        env_type = oauthmodel.EbayEnv.get_env(self.ebay_env)
        # TODOx
        if not self.ebay_auth_code:
            self.ebay_auth_url = self.generate_user_authorization_url(
                env_type, self.scope
            )
            access_code = self.get_authorization_code(self.ebay_auth_url)
            self.ebay_auth_code = access_code
        token = self.exchange_code_for_access_token(
            env_type=env_type, code=self.ebay_auth_code
        )
        params["headers"]["Authorization"] = f'Bearer {token["access_token"]}'

    def generate_user_authorization_url(self, env_type, scopes, state=None):
        """
        env_type = environment.SANDBOX or environment.PRODUCTION
        scopes = list of strings
        """

        scopes = " ".join(scopes)
        param = {
            "client_id": self.client_id,
            "redirect_uri": self.token_url,
            "response_type": "code",
            "prompt": "login",
            "scope": scopes,
        }

        if state != None:
            param.update({"state": state})

        query = url_encode(param)
        return env_type.web_endpoint + "?" + query

    def generate_local_url(self):
        env_type = oauthmodel.EbayEnv.get_env(self.ebay_env)
        self.ebay_auth_url = self.generate_user_authorization_url(env_type, self.scope)

    def decode_local_code(self):
        if self.ebay_auth_code:
            cd = url_decode(self.ebay_auth_code)
            self.ebay_auth_code = cd.get("code")

    def get_application_token(self, env_type, scopes):
        """
        makes call for application token and stores result in credential object
        returns credential object
        """

        headers = util._generate_request_headers(self.client_id, self.client_secret)
        body = util._generate_application_request_body(self.token_url, " ".join(scopes))

        resp = requests.post(env_type.api_endpoint, data=body, headers=headers)
        content = json.loads(resp.content)
        token = oauthmodel.oAuth_token()

        if resp.status_code == requests.codes.ok:
            token.access_token = content["access_token"]
            # set token expiration time 5 minutes before actual expire time
            token.token_expiry = (
                datetime.utcnow()
                + timedelta(seconds=int(content["expires_in"]))
                - timedelta(minutes=5)
            )

        else:
            token.error = str(resp.status_code) + ": " + content["error_description"]
        return token

    def exchange_code_for_access_token(self, env_type, code):

        headers = util._generate_request_headers(self.client_id, self.client_secret)
        body = util._generate_oauth_request_body(self.token_url, code)
        resp = requests.post(env_type.api_endpoint, data=body, headers=headers)

        content = json.loads(resp.content)
        token = oauthmodel.oAuth_token()

        if resp.status_code == requests.codes.ok:
            token.access_token = content["access_token"]
            token.token_expiry = (
                datetime.now()
                + timedelta(seconds=int(content["expires_in"]))
                - timedelta(minutes=5)
            )
            token.refresh_token = content["refresh_token"]
            token.refresh_token_expiry = (
                datetime.now()
                + timedelta(seconds=int(content["refresh_token_expires_in"]))
                - timedelta(minutes=5)
            )
        else:
            token.error = str(resp.status_code) + ": " + content["error_description"]
            raise Exception(token.error)
        return token.access_token

    def get_access_token(self, env_type, refresh_token, scopes):
        """
        refresh token call
        """

        headers = util._generate_request_headers(self.client_id, self.client_secret)
        body = util._generate_refresh_request_body(" ".join(scopes), refresh_token)
        resp = requests.post(env_type.api_endpoint, data=body, headers=headers)
        content = json.loads(resp.content)
        token = oauthmodel.oAuth_token()
        token.token_response = content

        if resp.status_code == requests.codes.ok:
            token.access_token = content["access_token"]
            token.token_expiry = (
                datetime.now()
                + timedelta(seconds=int(content["expires_in"]))
                - timedelta(minutes=5)
            )
        else:
            token.error = str(resp.status_code) + ": " + content["error_description"]
        return token

    def get_authorization_code(self, signin_url):

        userid = self.ebay_user_id
        password = self.ebay_user_pw

        browser = webdriver.Chrome()
        browser.get(signin_url)
        time.sleep(5)

        form_userid = browser.find_element_by_name("userid")
        form_pw = browser.find_element_by_name("pass")

        form_userid.send_keys(userid)
        form_pw.send_keys(password)

        browser.find_element_by_id("sgnBt").submit()

        time.sleep(5)

        url = browser.current_url
        browser.quit()

        if "code=" in url:
            code = re.findall("code=(.*?)&", url)[0]
        else:
            raise Exception("Error while finding Code")

        decoded_code = urllib.unquote(code).decode("utf8")
        return decoded_code
