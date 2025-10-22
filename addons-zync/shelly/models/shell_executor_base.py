import tempfile
import os
import traceback
import base64
import arrow
import uuid
from contextlib import contextmanager
import threading
from sarge import Capture, run
from odoo.exceptions import UserError
import time
from copy import deepcopy
from pathlib import Path
import logging

try:
    from odoo.addons.queue_job.exception import RetryableJobError
except ImportError:

    class RetryableJobError(Exception):
        pass


logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 24 * 3600


def duration(d):
    return (arrow.get() - d).total_seconds()


class MyWriter:
    def __init__(self, ttype, logger, logoutput):
        self.text = [""]
        self.ttype = ttype
        self.line = ""
        self.logger = logger
        self.logoutput = logoutput
        self.filepath = tempfile.mktemp(suffix="shellwriter.log")
        self.file = open(self.filepath, "a+")

    def __del__(self):
        self.cleanup()

    def cleanup(self):
        try:
            if not self.file.closed:
                self.file.close()
            path = Path(self.filepath)
            if path.exists():
                path.unlink()
        except Exception:
            msg = traceback.format_exc()
            logger.error(msg)

    def get_all_lines(self):
        self.file.seek(0)
        return self.file.read()

    def write(self, line):
        if line is None:
            return
        line = line.decode("utf-8")
        self.file.write(line)
        if line.endswith("\n"):
            line = line[:-1]
        if self.logoutput and self.logger:
            if self.ttype == "error":
                self.logger.error(line)
            else:
                self.logger.info(line)


class BaseShellExecutor:
    class TimeoutConnection(Exception):
        pass

    class TimeoutFinished(Exception):
        pass

    def __init__(
        self,
        ssh_keyfile,
        host,
        cwd,
        env=None,
        user=None,
    ):
        self.host = host
        self._cwd = Path(cwd) if cwd else None
        self.env = env or {}
        if env:
            assert isinstance(env, dict)
        self.ssh_keyfile = ssh_keyfile
        self.user = user
        if not user:
            raise Exception("User required!")

    @property
    def cwd(self):
        return self._cwd

    def set_cwd(self, value):
        self._cwd = value

    def _internal_execute(
        self,
        cmd,
        cwd=None,
        env=None,
        logoutput=True,
        timeout=None,
    ):
        """
        Problem observed: Permission denied, please try again
        Is nerving at deployments where many steps happen and then this error comes.
        """

        MAX_RETRY_ON_PERMISSION_DENIED_ERROR = 10

        if timeout is None:
            timeout = DEFAULT_TIMEOUT

        # region: conversions
        def convert_path(x):
            if isinstance(x, Path):
                x = str(x)
            return x

        if not isinstance(cmd, str):
            cmd = list(map(convert_path, filter(bool, cmd)))

        if isinstance(cmd, (tuple, list)):

            def format_cmd_part(x):
                if x == "|":
                    return x
                if "'" not in x:
                    return f'"{x}"'
                else:
                    return x

            cmd = f"{cmd[0]} " + " ".join(map(format_cmd_part, cmd[1:]))
        # use login shell for estables path env
        # problems on bash when git format='  is there because of apostrophe; this way was safe
        cmd = base64.b64encode(("#!/bin/bash -l\n" + cmd).encode("utf8"))
        cmd_filename = f"/tmp/{uuid.uuid4()}.v2.cmd"
        self.put(cmd, cmd_filename)
        # endregion

        # region: Writer Class

        stdwriter = MyWriter("info", self.get_logger(), logoutput)
        errwriter = MyWriter("error", self.get_logger(), logoutput)

        # endregion

        sshcmd = self._get_ssh_client()
        stop_marker = str(uuid.uuid4()) + str(uuid.uuid4())
        start_marker = str(uuid.uuid4()) + str(uuid.uuid4())

        # region: start collecting threads
        stdout = Capture(buffer_size=-1)  # line buffering
        stderr = Capture(buffer_size=-1)  # line buffering
        data = {
            "stop": False,
            "started": False,
            "stop_marker": False,
        }

        def on_started():
            data["started"] = True

        def on_stop_marker():
            data["stop_marker"] = arrow.get()

        def collect(
            capture,
            writer,
            marker=None,
            on_marker=None,
            stop_marker=None,
            on_stop_marker=None,
        ):
            while not data["stop"]:
                for line in capture:
                    line_decoded = line.decode("utf-8")
                    is_marker = False
                    if marker and marker in line_decoded and on_started:
                        on_marker()
                        is_marker = True
                    if stop_marker and stop_marker in line_decoded and on_stop_marker:
                        on_stop_marker()
                        is_marker = True

                    if not is_marker:
                        writer.write(line)

        tstd = threading.Thread(
            target=collect,
            args=(
                stdout,
                stdwriter,
                start_marker,
                on_started,
                stop_marker,
                on_stop_marker,
            ),
        )

        terr = threading.Thread(target=collect, args=(stderr, errwriter))
        tstd.daemon = True
        terr.daemon = True
        [x.start() for x in [tstd, terr]]  # NOQA
        # endregion

        # region: build command chain
        bashcmd = "#!/bin/bash\n" "set -o pipefail\n"

        cwd = cwd or self._cwd
        if cwd:
            bashcmd += (
                "function wait_for_dir {        \n"
                '  deadline=$(date --date " + 30 seconds" +"%Y%m%d%H%M%S") \n'
                '  while [ "$(date +"%Y%m%d%H%M%S")" -lt "${deadline}" ]; do \n'
                f'   if [[ -d "{cwd}" ]]; then  \n'
                "       break                   \n"
                "    fi                         \n"
                "  done                         \n"
                "}                              \n\n"
                f"export INITIAL_PWD='{cwd}'\n"
                "wait_for_dir\n"
                f"cd '{cwd}' || exit 15\n"
            )

        effective_env = deepcopy(self.env or {})
        if env:
            effective_env.update(env)
        for k, v in effective_env.items():
            bashcmd += f'export {k}="{v}"\n'

        bashcmd += (
            f"echo '{start_marker}'\n"
            f"touch ~/.hushlogin  # suppress motd "
            "to correctly parse git outputs\n"
            f"logger 'SHELLY COMMAND: {cmd}'\n"
            f"set -e\n"
            f"chmod a+x '{cmd_filename}'\n"
            f"cat {cmd_filename} | base64 --decode | /bin/bash -l | cat -\n"
            f"echo\n"
            f"echo 1>&2\n"
            f"[[ -e '{cmd_filename}' ]] && rm '{cmd_filename}'\n"
            f"echo '{stop_marker}' \n"
        )
        # endregion

        # region: run command
        p = run(
            sshcmd,
            async_=True,
            stdout=stdout,
            stderr=stderr,
            env=effective_env,
            input=bashcmd,
        )
        deadline_started = arrow.get().shift(seconds=60)
        while True:
            if p.returncodes and any(x is not None for x in p.returncodes):
                break
            if arrow.get() > deadline_started:
                raise RetryableJobError(
                    "Timeout starting command on remote machine",
                    seconds=10,
                    ignore_retry=True,
                )
            if data["started"]:
                break
            if p.commands:
                p.commands[0].poll()

        deadline = arrow.get().shift(seconds=timeout)
        timeout_happened = False
        try:
            if not p.commands:
                raise Exception(f"Command failed: {cmd}")
            while True:
                p.commands[0].poll()

                if (
                    p.commands[0].returncode is not None
                    and not p.commands[0].returncode
                    and data.get("stop_marker")
                ):
                    # Perfect End
                    break

                if p.commands[0].returncode is not None and p.commands[0].returncode:
                    break

                if arrow.get() > deadline:
                    p.commands[0].kill()
                    timeout_happened = True
                    p.commands[0].kill()
                    break
                time.sleep(0.05)

                if data.get("stop_marker"):
                    if duration(data["stop_marker"]) > 10 and not p.returncodes:
                        break
                if p.commands[0].returncode is not None and not data.get("stop_marker"):
                    data.setdefault("waiting_for_stop", arrow.get())
                    if duration(data["waiting_for_stop"]) > 5:
                        break

        finally:
            data["stop"] = True
        tstd.join()
        terr.join()
        # endregion

        # region: evaluate run result
        stdout = stdwriter.get_all_lines()
        stderr = errwriter.get_all_lines()

        stdwriter.cleanup()
        errwriter.cleanup()

        if p.returncodes:
            return_code = p.returncodes[0]
        elif data.get("stop_marker"):
            # script finished but ssh didnt get it
            return_code = 0
            if stderr.endswith("\n"):
                stderr = stderr[:-1]
        else:
            raise BaseShellExecutor.TimeoutFinished()

        # remove last line from bashcmd if good:
        if return_code == 0 and stdout.endswith("\n"):
            stdout = stdout[:-1]
        # endregion

        # cleanup command file:
        run(
            sshcmd,
            async_=False,
            input=f"[[ -e '{cmd_filename}' ]] && rm '{cmd_filename}'",
        )

        return {
            "timeout": timeout_happened,
            "exit_code": p.commands[0].returncode,
            "stdout": stdout,
            "stderr": stderr,
        }

    def _get_ssh_client(self, cmd="ssh", split_host=False):
        host = self.host
        user = self.user
        base = (
            f"{cmd} "
            f"-T "
            # f"-oControlPath ~/.ssh/controlmasters/%r@%h:%p "
            # f"ControlMaster=auto "
            # f"ControlPersist=10m "
            f"-oBatchMode=yes "
            f"-oStrictHostKeyChecking=no "
            f"-oLogLevel=ERROR "
        )
        if self.ssh_keyfile:
            base += f" -i {self.ssh_keyfile} "
        user_host = f"{user}@{host}"
        if split_host:
            return base, user_host
        return base + " " + user_host + " "

    def get_logger(self):
        return logger

    def download(self, source, dest):
        # not tested yet

        if not str(source).startswith("/"):
            source = Path(self._cwd) / str(source)

        cmd, host = self._get_ssh_client("scp", split_host=True)
        capt = Capture()
        p = run(cmd + f" '{host}:{source}' '{dest}'", stdout=capt, stderr=capt)
        if p.commands[0].returncode:
            raise Exception("Copy failed")

    def get(self, source):
        filename = Path(tempfile.mktemp(suffix="."))
        self.download(source, filename)
        try:
            return filename.read_bytes()
        finally:
            if filename.exists():
                filename.unlink()

    def upload(self, source, dest, auto_retry=5):
        cmd, host = self._get_ssh_client("scp", split_host=True)
        capt = Capture()
        err = ""
        for i in range(auto_retry or 0):
            p = run(cmd + f" '{source}' '{host}:{dest}'", stdout=capt, stderr=capt)
            if p.commands[0].returncode:
                err = capt.readlines()
                time.sleep(3)
            else:
                break
        else:
            raise Exception(f"Transfer failed to {host}:{dest}\n{err}")

    def put(self, content, dest):
        if "~" in str(dest):
            dest = str(dest).replace("~", self._get_home_dir())
        dest = Path(dest)
        if self.cwd:
            dest = self.cwd / Path(dest)
        filename = Path(tempfile.mktemp(suffix="."))
        if isinstance(content, str):
            content = content.encode("utf-8")
        filename.write_bytes(content)
        try:
            self.upload(filename, dest)
        finally:
            filename.unlink()

    def extract_zip(self, content, dest_path):
        assert dest_path not in ["/", "/var/"]
        assert len(Path(dest_path).parts) > 2

        with self.machine._temppath(
            usage="srcfile", maxage=dict(hours=1)
        ) as remote_temp_path:
            self.X(["mkdir", "-p", remote_temp_path])
            filename = remote_temp_path / "src.tar.gz"

            self.put(content, filename)
            with self.machine._temppath(
                usage="srcfile", maxage=dict(hours=1)
            ) as temppath:
                self.X(["mkdir", "-p", temppath])
                self.X(["tar", "xfz", filename, "--no-same-owner"], cwd=temppath)
                self.X(
                    [
                        "rsync",
                        str(temppath) + "/",
                        str(dest_path) + "/",
                        # a requierd; otherwise some files were missed to transfer
                        "-ar",
                        "--delete-after",
                    ]
                )

    def get_zipped(self, path, excludes=None):
        from ..exceptions import ShellExecuteError

        excludes = excludes or []
        with self.machine._temppath(usage="get_zipped") as filename:
            zip_cmd = ["tar", "cfz", filename, "-C", path, "."]
            for exclude in excludes:
                zip_cmd.insert(-1, f'--exclude="{exclude}"')
            with self.clone(cwd=path) as self2:
                counter = 0
                while True:
                    try:
                        self2.X(zip_cmd)
                    except ShellExecuteError as ex:
                        if "file changed as we read it" in str(ex):
                            counter += 1
                            if counter > 20:
                                raise Exception(
                                    f"Timeout trying to zip {path} for {counter} tries."
                                ) from ex
                            time.sleep(counter * 5)
                        else:
                            raise
                    else:
                        break
            content = self.get(filename)
            return content

    def safe_move_directory(self, src, dest):
        src = Path(src)
        dest = Path(dest)

        # if on different directories, move to intermediate just before
        # hoping to be on same disk
        tmpdest = dest.parent / (dest.name + f".mv.{uuid.uuid4()}")

        # keep directory ID for running processes; probably files vanished in between,
        # then catch that error
        if self.exists(dest):
            self.remove(dest)

        try:
            self.X(["mv", src, tmpdest], allow_error=True)
            if self.exists(src):
                self.X(["rsync", str(src) + "/", str(tmpdest) + "/", "-ar"])
                self.remove(src)

            self.X(["mv", tmpdest, dest], allow_error=True)
        finally:
            self.rm(tmpdest)

    def file_size(self, path):
        size = self.X(["stat", "-c", "%s", path])["stdout"].strip()
        size = int(size or 0)
        return size

    def get_date_modified(self, path):
        seconds = int(self.X(["stat", "-c", "%Y", path])["stdout"].strip())
        return arrow.get(seconds)

    def get_age_hours(self, path):
        return (arrow.get() - self.get_date_modified(path)).total_seconds() / 3600

    def md5sum(self, path):
        return self.X(["md5sum", path])["stdout"].strip().split(" ")[0]

    def X_multiline(
        self,
        commands,
        allow_error=False,
        env=None,
        cwd=None,
        logoutput=True,
        timeout=None,
        retry=None,
        retry_wait=10,
    ):
        cmdfilename = f"/tmp/{uuid.uuid4()}"
        try:
            self.put("\n".join(commands), cmdfilename)
            self.X(["/bin/bash", cmdfilename])
        finally:
            self.remove(cmdfilename)

    def X(
        self,
        cmd,
        allow_error=False,
        env=None,
        cwd=None,
        logoutput=True,
        timeout=None,
        retry=None,
        retry_wait=10,
    ):
        from ..exceptions import ShellExecuteError

        retry = retry or 0
        effective_env = deepcopy(self.env)
        if env:
            effective_env.update(env)
        for i in range((retry or 0) + 1):
            res = self._internal_execute(
                cmd, cwd=cwd, env=env, logoutput=logoutput, timeout=timeout
            )
            # TODO make catch common error func
            if res["exit_code"]:
                if ".git/index.lock" in res["stderr"]:
                    if not retry:
                        retry = 5
                    time.sleep(5)

            if res["exit_code"]:
                if i == retry:
                    break
            else:
                break
            time.sleep(retry_wait)

        if not allow_error:
            if res["exit_code"] is None:
                raise TimeoutError(f"Timeout happend: {cmd}")
            if res["exit_code"]:
                raise ShellExecuteError(
                    f"Error happened: {res['exit_code']} at {self.cwd or 'no cwd'}:\n"
                    f"{res['stderr']}\n"
                    f"{res['stdout']}",
                    res["exit_code"],
                    res["stdout"],
                    res["stderr"],
                )

        return res

    def _get_home_dir(self):
        res = self._internal_execute(
            ["echo", "$HOME"], cwd="/", env=self.env, logoutput=False, timeout=10
        )["stdout"].strip()
        if res.endswith("/~"):
            res = res[:-2]
        return res

    @property
    def cwd(self):
        return self._cwd

    def exists(self, path, glob=False):
        if not glob:
            res = self._internal_execute(["test", "-e", path], logoutput=False)
            return res["exit_code"] == 0
        path = path.replace(" ", "\\ ")
        res = self._internal_execute(f"ls {path}", logoutput=False)
        return res["stdout"].strip().splitlines()

    def rm(self, path):
        return self.remove(path)

    def remove(self, path):
        if "~" in str(path):
            path = str(path).replace("~", self._get_home_dir())
        if not self.exists(path):
            return
        if self.logsio:
            self.logsio.info(f"Path {path} exists and is erased now.")
        path = Path(path)
        tmp = path.parent / (path.name + f".tmp.{uuid.uuid4()}")
        self._internal_execute(["mv", path, tmp])
        self._internal_execute(["rm", "-Rf", tmp])

        if self.exists(tmp):
            self._internal_execute(["sudo", "rm", "-Rf", tmp])

        if self.exists(path):
            raise UserError(f"Removing of {tmp} failed.")

    def mkdir(self, path, parents=True):
        cmd = ["mkdir", path]
        if parents:
            cmd += ["-p"]
        res = self._internal_execute(cmd)
        if res['exit_code']:
            raise Exception(f"Failed to create the directory {path}")

    def is_file(self, path):
        res = self._internal_execute(["test", "-f", path], logoutput=False)
        return not res['exit_code']

    def is_dir(self, path):
        res = self._internal_execute(["test", "-d", path], logoutput=False)
        return not res['exit_code']