# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import os
import tempfile
from pathlib import Path
import subprocess
from odoo import fields, models
from odoo.addons.shelly.models.shell_executor_base import BaseShellExecutor


class Shell(models.Model):
    _inherit = "zbs.worker"
    _name = "zbs.shell"
    _description = "Shell/Bash"

    code = fields.Text("Code", tracking=True)

    ssh_username = fields.Char("SSH Username", required=False, tracking=True)
    ssh_host = fields.Char("SSH Host", required=False, tracking=True)
    ssh_port = fields.Integer("SSH Port", default=22, required=False, tracking=True)
    ssh_private_key = fields.Text("SSH Private Key")
    ssh_pubkey = fields.Text("SSH Public Key", tracking=True)
    cwd = fields.Char("Working Directory")

    def make_keys(self):
        # privkey, pubkey = self.env["rsa.helper"]._generate_key(4096)
        # self.ssh_private_key = privkey
        # self.ssh_pubkey = pubkey

        filename = Path(tempfile.mktemp())
        if filename.exists():
            filename.unlink()

        subprocess.run(
            [
                "ssh-keygen",
                "-t",
                "ed25519",
                "-f",
                filename,
                "-q",
                "-N",
                "",
            ],
            check=True,
        )
        self.ssh_private_key = filename.read_text()
        self.ssh_pubkey = filename.with_suffix(".pub").read_text()

    def process_record(self, instance, index, record, data, errors=None):
        keyfile = Path(tempfile.mktemp())
        keyfile.write_text(self.ssh_private_key)
        os.chmod(keyfile, 0o400)

        code = self.code
        try:
            executor = BaseShellExecutor(
                ssh_keyfile=keyfile,
                host=self.ssh_host,
                cwd=self.cwd or "/tmp",
                user=self.ssh_username,
                env={},
            )
            env = {}
            instance_env = instance._get_env()
            self._fill_env(env, instance_env)
            if not isinstance(data, models.BaseModel):
                self._fill_env(env, data)
                if record:
                    self._fill_env(env, record)

            res = executor.X(code, env=env)

            def post_console_out(output):
                instance.message_post(body=f"<pre>{output}</pre>")

            post_console_out(res["stdout"])
            if res["stderr"].strip():
                post_console_out(res["stderr"])

            return res
        finally:
            keyfile.unlink()

    def _fill_env(self, env, data):
        data = self.env["zebrooset"].rs(data)
        for index, rec in data._iterate_records():
            for k in rec._keys():
                env[k] = str(rec[k])
        return env
