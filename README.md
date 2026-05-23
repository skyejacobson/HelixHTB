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

We can attempt to go to `http://10.129.2.74` but the browser wont redirect us. We need to first add `helix.htb` and the corresponding IP to `/etc/hosts`.

Once adding the hostname to the hosts file we can see a cybersecurity organization website with very little control availability. There are 2 buttons that when activated and inspected don't call anything and are red herrings. We can enumerate further with `ffuf` and `feroxbuster`.

Both `ffuf` and `feroxbuster` dont reveal any information subdirectory wise but `ffuf` allows us to find a hidden subdomain called `flow.helix.htb`.

```
┌──(root㉿kali-linux-2024-2)-[/home/parallels/Documents/Helix]
└─# ffuf -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -u http://helix.htb -H "Host: FUZZ.helix.htb" -s -mc 200
flow
```

When we access the 
