from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import uuid
import os
import tempfile
import subprocess
from .shell_executor_base import BaseShellExecutor
from pathlib import Path
from contextlib import contextmanager
import shutil


@contextmanager
def tempdir():
    dir = Path(tempfile.mktemp(suffix="."))
    try:
        dir.mkdir(exist_ok=True, parents=True)
        yield Path(dir)
    finally:
        shutil.rmtree(dir)


class OperatorHost(models.AbstractModel):
    _name = "shell.operator.host"
    _description = "Shell Operator Host"

    host = fields.Char("IP")
    username = fields.Char("Username")

    private_key = fields.Text("Key")
    public_key = fields.Text("Pub Key")
    ttype = fields.Selection(
        [("rsa", "RSA"), ("ed25519", "ed25519")],
        required=True,
        default="ed25519",
        string="Type (ed25519 incompatible with azure)",
    )

    @contextmanager
    def _shell(self, cwd=None, env=None):
        self.ensure_one()
        home = os.environ["HOME"]
        file = Path(home) / f".ssh/{uuid.uuid4()}.key"
        file.parent.mkdir(exist_ok=True)
        file.write_text(self.private_key)
        os.chmod(file, 0o400)
        try:
            yield BaseShellExecutor(
                file, self.host, user=self.username, env=env, cwd=cwd
            )
        finally:
            if file.exists():
                file.unlink()

    def generate_ssh_key(self):
        self.ensure_one()
        with tempdir() as dir:
            cmd = ["-f", "temp", "-P", ""]
            if self.ttype:
                cmd += ["-t", self.ttype]
            subprocess.check_call(
                ["/usr/bin/ssh-keygen"] + cmd,
                cwd=dir,
            )
            keyfile = dir / "temp"
            pubkeyfile = dir / "temp.pub"
            self.private_key = keyfile.read_text()
            self.public_key = pubkeyfile.read_text()

    def test_ssh(self):
        with self._shell() as shell:
            shell.X(["ls"])
        raise ValidationError(_("Everyhing Works!"))
