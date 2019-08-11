import re
import xml
import winrm
import requests
from base64 import b64encode
from riposte import Riposte

p = winrm.protocol.Protocol(
    endpoint='',
    transport='',
    username=r'',
    password='',
    server_cert_validation=''
)

pyshellrm = Riposte(prompt="pyshellrm:~$ ")
CUR_SHELL = None
SHELL_IDS = []

upload_tpl = '''\
$to = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath("DEST")
$parent = Split-Path $to
if(!(Test-path $parent)) { mkdir $parent | Out-Null }
$fileStream = New-Object -TypeName System.IO.FileStream -ArgumentList @(
    $to,
    [system.io.filemode]::Append,
    [System.io.FileAccess]::Write,
    [System.IO.FileShare]::ReadWrite
)
$bytes=[Convert]::FromBase64String('BYTES')
$fileStream.Write($bytes, 0, $bytes.length)
$fileStream.Dispose()
'''

def shell_required(fn):
    def wrapper(*args, **kwargs):
        if CUR_SHELL is None:
            pyshellrm.error("No active session")
            return
        return fn(*args, **kwargs)
    return wrapper

def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]

def clean_error(msg):

    def strip_namespace(msg):
        p = re.compile(b"xmlns=*[\"\"][^\"\"]*[\"\"]")
        allmatches = p.finditer(msg)
        for match in allmatches:
            msg = msg.replace(match.group(), b"")
        return msg

    if msg.startswith(b"#< CLIXML\r\n"):
        msg_xml = msg[11:]
        msg_xml = strip_namespace(msg_xml)
        root = xml.etree.ElementTree.fromstring(msg_xml)
        nodes = root.findall("./S")
        new_msg = ""
        for s in nodes:
            new_msg += s.text.replace("_x000D__x000A_", "\n")
        if len(new_msg):
            return new_msg.strip()

    return msg.decode('utf-8').strip()

def run_cmd(command, args=()):
    try:
        command_id = p.run_command(CUR_SHELL, command, args)
        rs = winrm.Response(p.get_command_output(CUR_SHELL, command_id))
        p.cleanup_command(CUR_SHELL, command_id)
    except winrm.exceptions.WinRMTransportError:
        return winrm.Response((None, b"Transport Error", None))
    return rs

def run_ps(script):
    script = '$ProgressPreference = "SilentlyContinue";' + script
    encoded_ps = b64encode(script.encode('utf_16_le')).decode('ascii')
    resp = run_cmd('powershell -encodedcommand {0}'.format(encoded_ps))
    if resp.std_out:
        pyshellrm.success(resp.std_out.decode('utf-8'))
    if resp.std_err:
        pyshellrm.error(clean_error(resp.std_err))

@pyshellrm.command("exit")
def exit():
    raise StopIteration

@pyshellrm.command("quit")
def quit():
    raise StopIteration

@pyshellrm.command("close")
@shell_required
def close():
    try:
        global CUR_SHELL
        p.close_shell(CUR_SHELL)
        CUR_SHELL = None
    except winrm.exceptions.WinRMTransportError as e:
        pyshellrm.error(e)

@pyshellrm.command("shell")
@shell_required
def shell():
    while True:
        try:
            run_ps(input("PS> "))
        except KeyboardInterrupt:
            pyshellrm.info("Exiting PS shell")
            break

@pyshellrm.command("upload")
@shell_required
def upload(local_path: str, remote_path: str):
    pyshellrm.status(f"Uploading file {local_path} to {remote_path}")

    with open(local_path, 'rb') as f:
        local_file = f.read()

    new_tpl = upload_tpl.replace("DEST", remote_path)
    chunk_list = list(chunks(local_file, 1750))
    for idx, chunk in enumerate(chunk_list):
        pyshellrm.info(f"Sending chunk [{idx}/{len(chunk_list)-1}]")
        run_ps(new_tpl.replace("BYTES", b64encode(chunk).decode('ascii')))

@pyshellrm.command("unset")
def unset_shell():
    global CUR_SHELL
    CUR_SHELL = None

@pyshellrm.command("set")
def set_shell(shell: str):
    global CUR_SHELL
    if shell not in SHELL_IDS:
        pyshellrm.error(f"{shell} not in shell list.")
        return
    CUR_SHELL = shell
    pyshellrm.info(f"Current Shell: {CUR_SHELL}")

@pyshellrm.complete("set")
def set_completer(text, line, start_index, end_index):
    return [
        shell_id
        for shell_id in SHELL_IDS
        if shell_id.startswith(text)
    ]

@pyshellrm.command("list")
def list_sessions():
    if not SHELL_IDS:
        pyshellrm.error("No active sessions")
    else:
        pyshellrm.info(*SHELL_IDS)

@pyshellrm.command("connect")
def connect():
    global SHELL_IDS
    pyshellrm.status(f"Connecting to {p.transport.endpoint}")
    try:
        SHELL_IDS.append(p.open_shell())
    except requests.exceptions.ConnectTimeout:
        pyshellrm.error(f"Failed to connect to {p.transport.endpoint}")
        return
    except winrm.exceptions.WinRMTransportError as e:
        pyshellrm.error(e)
        return
    except winrm.exceptions.InvalidCredentialsError as e:
        pyshellrm.error(e)
        return
    except winrm.exceptions.WinRMError as e:
        pyshellrm.error(e)
        return
    pyshellrm.success(f"Connected to {p.transport.endpoint}")

pyshellrm.run()
