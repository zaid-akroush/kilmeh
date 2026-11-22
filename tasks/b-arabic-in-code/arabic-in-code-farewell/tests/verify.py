# Harbor verifier body. Runs in the container with the python3 stdlib only (`python3 -S`, see
# test.sh). Never imports the app: tests/worker.py does, as uid 65534 in a new session when
# root, and this process compares its raw outputs.
#
# Why a forged worker output cannot pass: the agent's code shares the worker's process, so it
# can write anything to the worker's channel. But the names are drawn here at random for each
# run, so the only output that passes is the right farewell and greeting for names the code
# never saw: the task's behaviour. Remaining limit: code in the worker could still read the
# names from the worker's own memory.
#
# Fails closed: the tests directory must be owned by this user with no group/other access
# (test.sh locks it), or verify exits 2 before any agent code runs.
import json
import os
import secrets
import signal
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True  # a new __pycache__ would unlock tests/ (see unlocked_path)
sys.path.insert(0, HERE)
from checks import check_integrity  # noqa: E402

APP = os.environ.get("KILMEH_APP", "/app")
G = os.path.join(HERE, "golden")
ENV = {"PATH": "/usr/local/bin:/usr/bin:/bin"}
NOBODY = 65534
LETTERS = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"


def rb(p):
    with open(p, "rb") as f:
        return f.read()


def unlocked_path(root):
    """The first path under `root` another user could reach, or None when locked."""
    me = os.geteuid()
    for dirpath, dirnames, filenames in os.walk(root):
        for path in [dirpath, *(os.path.join(dirpath, n) for n in dirnames + filenames)]:
            st = os.lstat(path)
            if st.st_uid != me or st.st_mode & 0o077:
                return f"{path} (owner {st.st_uid}, mode {oct(st.st_mode & 0o7777)})"
    return None


def as_nobody():
    return {"user": NOBODY, "group": NOBODY, "extra_groups": []} if os.geteuid() == 0 else {}


def kill_nobody():
    """kill(-1) as uid 65534 signals every process of that uid, including daemons that left
    the worker's session. Only when root."""
    if os.geteuid() != 0:
        return
    for _ in range(3):
        subprocess.run(
            [sys.executable, "-I", "-S", "-c", "import os, signal; os.kill(-1, signal.SIGKILL)"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd="/",
            env=ENV,
            timeout=30,
            **as_nobody(),
        )


def run_worker(app, names):
    """Raw results from the worker, or None if it gave no answer."""
    proc = subprocess.Popen(
        [sys.executable, "-I", "-c", rb(os.path.join(HERE, "worker.py")).decode(), app],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        cwd=app,
        env=ENV,
        start_new_session=True,
        **as_nobody(),
    )
    try:
        out, _ = proc.communicate(json.dumps(names).encode(), timeout=60)
    except (subprocess.TimeoutExpired, OSError):
        out = b""
    finally:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except OSError:
            pass
        kill_nobody()
        proc.wait()
    try:
        return json.loads(out)
    except ValueError:
        return None


reachable = unlocked_path(HERE)
if reachable is not None:
    print(f"refusing to grade: grader files readable by others: {reachable}", file=sys.stderr)
    sys.exit(2)
names = os.listdir(APP)
main = rb(APP + "/تحية.py") if "تحية.py" in names else b""
res = check_integrity(rb(G + "/orig.py"), main, rb(G + "/README.md"), rb(APP + "/README.md"), names)
tries = ["سارة"] + ["".join(secrets.choice(LETTERS) for _ in range(3 + i)) for i in range(3)]
expected = [[["ok", f"وداعاً يا {n}!"], ["ok", f"مرحباً بك يا {n}!"]] for n in tries]
results = run_worker(APP, tries)
print("worker results:", results, file=sys.stderr)
res["farewell_works"] = results == expected
print(json.dumps(res, ensure_ascii=False, indent=1))
sys.exit(0 if all(res.values()) else 1)
