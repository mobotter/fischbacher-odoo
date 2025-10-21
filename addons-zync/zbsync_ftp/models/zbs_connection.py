# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import stat
import tempfile
import ssl

from pathlib import Path
from ftplib import FTP
import ftplib
import pysftp
from odoo import fields, models
from contextlib import contextmanager
import logging

logger = logging.getLogger("zync.ftp")


class FTPConnection(models.Model):
    _name = "zbs.connection.ftp"

    _inherit = [
        "zbs.connection",
        "zbs.connection.mixin.usernamepassword",
        "zbs.connection.mixin.hostport",
    ]
    _name = "zbs.connection.ftp"
    _description = "FTP-Connection"
    timeout = fields.Integer("Timeout", default=10)
    ttype = fields.Selection(
        [("ftp", "FTP"), ("sftp", "SFTP"), ("ftps", "FTPS")],
        string="Type",
        required=True,
    )
    port = fields.Integer(default=21)
    username = fields.Char(required=False)
    password = fields.Char(required=False)

    @property
    def ftpObject(self):
        if self.ttype == "ftp":
            return Ftp(
                self.host,
                self.username,
                self.password,
                self.port,
                timeout=self.timeout,
            )
        elif self.ttype == "sftp":
            return Sftp(
                self.host,
                self.username,
                self.password,
                self.port,
                timeout=self.timeout,
            )
        elif self.ttype == "ftps":
            return Ftps(
                self.host,
                self.username,
                self.password,
                self.port,
                timeout=self.timeout,
            )

        else:
            raise NotImplementedError()


class Ftp:
    def __init__(self, hostname, username, password, port=22, timeout=10, sftp=False):
        """Constructor Method"""
        # Set connection object to None (initial value)
        self.connection = None
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self.timeout = timeout
        self.sftp = sftp
        self.pwd = None

    @contextmanager
    def connect(self):
        self.connection = FTP()
        self.connection.connect(
            host=self.hostname, port=self.port, timeout=self.timeout
        )
        self.connection.login(user=self.username, passwd=self.password)
        self.pwd = self.connection.pwd
        yield
        self.connection.quit()

    def delete_file(self, path):
        self.connection.delete(path)

    def list_files(self, path, recursive=False):
        all_contents, n_all_contents = [], []
        files, dirs = [], []
        self.connection.cwd(path)
        self.connection.retrlines("LIST", all_contents.append)
        self.connection.retrlines("NLST", n_all_contents.append)

        for i, item in enumerate(all_contents):
            item_l = item
            item_nl = n_all_contents[i]
            assert item_l.endswith(item_nl)
            if item.startswith("d"):
                dirs.append(item_nl)
                if recursive:
                    files += self.list_files(f"{path}/{item_nl}")
            else:
                files.append(f"{path}/{item_nl}")

        return files

    def download_file(self, filename):
        file = Path(tempfile.mktemp(suffix="."))
        try:
            with open(file, "wb") as local_file:
                self.connection.retrbinary(f"RETR {filename}", local_file.write)
            return file.read_bytes()
        finally:
            if file.exists():
                file.unlink()

    def exists(self, path):
        if path == "/":
            return "d"
        path = self._make_absolute(path)
        parent_path = str(Path(path).parent)
        name = Path(path).name
        all_contents, n_all_contents = [], []
        files, dirs = [], []
        self.connection.cwd(parent_path)
        self.connection.retrlines("LIST", all_contents.append)
        self.connection.retrlines("NLST", n_all_contents.append)
        for i, n_all in enumerate(n_all_contents):
            if n_all == name:
                return "d" if all_contents[i].startswith("d") else "f"

    def upload_file(self, filepath, content):
        filepath = self._make_absolute(filepath)
        file = Path(tempfile.mktemp(suffix="."))
        file.write_bytes(content)
        try:
            with open(file, "rb") as f:
                filepath = Path(filepath)
                self.connection.cwd(str(filepath.parent))
                self.connection.storbinary(f"STOR {filepath.name}", f)
        finally:
            if file.exists():
                file.unlink()

    def mkdir(self, path):
        path = self._make_absolute(path)
        path = Path(path)
        for i in range(len(path.parts) + 1):
            if i <= 1:
                continue
            _path = "/" + "/".join(path.parts[1:i])
            if not _path:
                continue
            if not self.exists(_path):
                self.connection.mkd(_path)

    def _make_absolute(self, path):
        if not path.startswith("/"):
            path = self.pwd + "/" + path
            if path.startswith("//"):
                path = path[1:]
        return path

    def move_ftp_file(self, source_path, destination_path):
        content = self.download_file(source_path)
        exists = self.exists(destination_path)
        if not exists:
            self.mkdir(destination_path)
        if not exists or exists == "d":
            destination_path = str(Path(destination_path) / Path(source_path).name)
        self.upload_file(destination_path, content)
        self.delete_file(source_path)


class Ftps(Ftp):
    class ImplicitFTP_TLS(ftplib.FTP_TLS):
        """FTP_TLS subclass that automatically wraps sockets in SSL to support implicit FTPS."""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._sock = None

        @property
        def sock(self):
            """Return the socket."""
            return self._sock

        @sock.setter
        def sock(self, value):
            """When modifying the socket, ensure that it is ssl wrapped."""
            if value is not None and not isinstance(value, ssl.SSLSocket):
                value = self.context.wrap_socket(value)
            self._sock = value

    def __init__(self, hostname, username, password, port=22, timeout=10):
        super().__init__(
            hostname, username, password, port=port, timeout=timeout, sftp=False
        )

    @contextmanager
    def connect(self):
        """Connects to the sftp server and returns the sftp connection object"""

        # Get the sftp connection object
        client = Ftps.ImplicitFTP_TLS()
        client.connect(self.hostname, self.port)
        client.login(self.username, self.password)
        self.connection = client
        yield
        self.disconnect()

    def disconnect(self):
        """Closes the sftp connection"""
        self.connection.quit()
        logger.info(f"Disconnected from host {self.hostname}")


class Sftp(Ftp):
    def __init__(self, hostname, username, password, port=22, timeout=10):
        super().__init__(
            hostname, username, password, port=port, timeout=timeout, sftp=True
        )

    @contextmanager
    def connect(self):
        """Connects to the sftp server and returns the sftp connection object"""

        # Get the sftp connection object
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        self.connection = pysftp.Connection(
            host=self.hostname,
            username=self.username,
            password=self.password,
            port=self.port,
            cnopts=cnopts,
        )
        self.pwd = self.connection.pwd
        yield
        self.disconnect()

    def disconnect(self):
        """Closes the sftp connection"""
        self.connection.close()
        logger.info(f"Disconnected from host {self.hostname}")

    def exists(self, path):
        if path == "/":
            return "d"
        path = self._make_absolute(path)
        ttype = None
        try:
            self.connection.listdir_attr(str(path))
        except FileNotFoundError:
            items = self.connection.listdir_attr(str(Path(path).parent))
            item = [x for x in items if x.filename == Path(path).name]
            if item:
                if stat.S_ISDIR(item[0].st_mode):
                    ttype = "d"
                else:
                    ttype = "f"
        else:
            item = [path]
            ttype = "d"
        if item:
            return ttype

    def list_files(self, path, recursive=False):
        path = self._make_absolute(path)
        items = self.connection.listdir(path or "/")
        files, dirs = [], []
        for item in items:
            item = str(Path(path) / item)
            if self.connection.isdir(item):
                dirs.append(item)
                if recursive:
                    files += self.list_files(item, True)
            else:
                files.append(item)

        return files

    def download_file(self, filename):
        file = Path(tempfile.mktemp(suffix="."))
        try:
            self.connection.get(filename, file)
            return file.read_bytes()
        finally:
            if file.exists():
                file.unlink()

    def upload_file(self, filepath, content):
        filepath = self._make_absolute(filepath)
        file = Path(tempfile.mktemp(suffix="."))
        file.write_bytes(content)
        try:
            self.connection.put(file, filepath)
        finally:
            if file.exists():
                file.unlink()

    def mkdir(self, path):
        path = self._make_absolute(path)
        exists = self.connection.exists(path)
        if not exists:
            self.connection.mkdir(path)

    def delete_file(self, path):
        path = self._make_absolute(path)
        self.connection.remove(path)
