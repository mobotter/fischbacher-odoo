# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).import tempfile
import subprocess
from pathlib import Path
from contextlib import contextmanager
from odoo import api, models
import tempfile


class RsaHelper(models.AbstractModel):
    _name = "rsa.helper"
    _description = "RSA Helper"

    @contextmanager
    def _tempfile(self, filecontent):
        filepath = Path(tempfile._get_default_tempdir()) / next(
            tempfile._get_candidate_names()
        )
        file = Path(filepath)
        file.write_text(filecontent)
        try:
            yield str(filepath)
        finally:
            file.unlink()

    @api.model
    def _generate_key(self, size=1024):
        with self._tempfile("") as private_key_path:
            subprocess.run(
                ["openssl", "genrsa", "-out", private_key_path, str(size)],
                check=True,
            )
            private_key = Path(private_key_path).read_text()
            with self._tempfile("") as pub_key_path:
                subprocess.run(
                    [
                        "openssl",
                        "rsa",
                        "-in",
                        private_key_path,
                        "-pubout",
                        "-out",
                        pub_key_path,
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True,
                )
                pubkey = Path(pub_key_path).read_text()

        return private_key, pubkey

    @api.model
    def encrypt(self, text, pubkey):
        assert isinstance(text, bytes)
        with self._tempfile(pubkey) as filepath:
            output = subprocess.run(
                ["openssl", "rsautl", "-encrypt", "-pubin", "-inkey", filepath, "-ssl"],
                input=text,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False,
                check=True,
            )
            return output.stdout

    @api.model
    def decrypt(self, text, privatekey):
        # no create

        assert isinstance(text, bytes)
        with self._tempfile(privatekey) as filepath:
            output = subprocess.run(
                ["openssl", "rsautl", "-decrypt", "-inkey", filepath],
                input=text,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False,
                check=True,
            )
            return output.stdout.decode("utf-8")
