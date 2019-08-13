import argparse
import requests
from pathlib import Path
from riposte import Riposte
from ruamel.yaml import YAML
from pypsrp.client import Client
from requests_ntlm import HttpNtlmAuth

try:
    from requests_kerberos import HTTPKerberosAuth
    HAS_KERBEROS = True
except ImportError:
    HAS_KERBEROS = False

try:
    from requests_credssp import HttpCredSSPAuth
    HAS_CREDSSP = True
except ImportError:
    HAS_CREDSSP = False

pyshellrm = Riposte(prompt="pyshellrm:~$ ")
pyshellrm._parser.add_argument("config", help="path to config.yml")

CFG_HOSTS = None
HOST_CONN = None
CONNECTIONS = []

@pyshellrm.command("exit")
def exit():
    raise StopIteration

@pyshellrm.command("quit")
def quit():
    raise StopIteration

@pyshellrm.command("run")
def run(command: str):
    if HOST_CONN is None:
        pyshellrm.error("No set connection")
        return

    resp = HOST_CONN.execute_ps(command)
    out, stream, had_err = resp
    if out:
        pyshellrm.success(out)
    if had_err:
        for error in stream.error:
            pyshellrm.error(error)
    if not out and not had_err:
        pyshellrm.success("No data returned from command.")

@pyshellrm.command("download")
def download(remote_path: str, local_path: str):
    if HOST_CONN is None:
        pyshellrm.error("No set connection")
        return

    HOST_CONN.fetch(remote_path, local_path)

@pyshellrm.command("upload")
def upload(local_path: str, remote_path: str):
    if HOST_CONN is None:
        pyshellrm.error("No set connection")
        return

    HOST_CONN.copy(local_path, remote_path)

@pyshellrm.command("unset")
def unset():
    global HOST_CONN
    HOST_CONN = None

@pyshellrm.command("set")
def set(host: str):
    global HOST_CONN

    if not CONNECTIONS:
        return

    d = dict(CONNECTIONS)
    HOST_CONN = d[host]

@pyshellrm.complete("set")
def set_completer(text, line, start_index, end_index):
    return [
        host
        for host in dict(CONNECTIONS).keys()
        if host.startswith(text)
    ]

@pyshellrm.command("connect")
def connect(host: str):
    global CONNECTIONS

    if not test(host):
        return False

    _host = CFG_HOSTS[host]

    c = Client(
            server    = _host.get("server", None),
            port      = _host.get("port", 5985),
            path      = _host.get("path", "wsman"),
            username  = _host.get("username" , r''),
            password  = _host.get("password" , r''),
            auth      = _host.get("auth", "ntlm"),
            ssl       = _host.get("ssl", False),
    )

    CONNECTIONS.append((host, c))

    return True

@pyshellrm.complete("connect")
def connect_completer(text, line, start_index, end_index):
    return [
        host
        for host in CFG_HOSTS.keys()
        if host.startswith(text)
    ]

@pyshellrm.command("hosts")
def hosts():
    print(*CFG_HOSTS)

@pyshellrm.command("test-all")
def test_all():
    [test(host) for host in CFG_HOSTS]

@pyshellrm.command("test")
def test(host: str):
    session = requests.Session()
    session.verify = False

    _host = CFG_HOSTS.get(host, None)
    if not _host:
        pyshellrm.error("Invalid host name")
        return False

    server    = _host.get("server", None)
    port      = _host.get("port", 5985)
    path      = _host.get("path", "wsman")
    username  = _host.get("username" , r'')
    password  = _host.get("password" , r'')
    auth      = _host.get("auth", "ntlm")
    ssl       = _host.get("ssl", False)

    req_url  = "http://" if not ssl else "https://"
    req_url += f"{server}:{port}/{path}"

    if auth == "ntlm":
        session.auth = HttpNtlmAuth(username, password)
    elif auth == "kerberos":
        if not HAS_KERBEROS:
            pyshellrm.error(
                f"{auth} auth attempt without requests-kerberos installed"
            )
            return False
        session.auth = HTTPKerberosAuth()
    elif auth == "credssp":
        if not HAS_CREDSSP:
            pyshellrm.error(
                f"{auth} auth attempt without requests-credssp installed"
            )
            return False
        session.auth = HttpCredSSPAuth(f'{username}', f'{password}',
                               auth_mechanism='auto')

    try:
        if not session.post(req_url).ok:
            pyshellrm.error(
                f"Failed to auth with {host} using {username}:{password}"
            )
            return False
    except requests.exceptions.ConnectionError:
        pyshellrm.error(
            f"Failed to establish a connection to {host}"
        )
        return False

    pyshellrm.success(
        f"Successfully connected to {host} with {username}:{password}"
    )
    return True

@pyshellrm.complete("test")
def test_completer(text, line, start_index, end_index):
    return [
        host
        for host in CFG_HOSTS.keys()
        if host.startswith(text)
    ]

def get_config(config_path):
    global CFG_HOSTS

    config = Path(config_path)
    if not config.is_file():
        print("Config file not found.")
        quit()

    with open(config_path, 'r') as cfg:
        yaml = YAML(typ="safe")
        CFG_HOSTS = yaml.load(cfg)

    for key in CFG_HOSTS:
        if not "server" in CFG_HOSTS[key]:
            raise KeyError("server")

arguments = pyshellrm._parser.parse_args()
get_config(arguments.config)
pyshellrm.run()
