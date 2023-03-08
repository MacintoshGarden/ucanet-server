# Installation Example
In this example, the installation is made on a Linux server inside the home folder of the user ucanet.  
Make sure to set up the ucanet.ini properly, check further down for the default conf stuff.

Living under the assumption that Python is already installed.

1. Add the user  
```sudo useradd -m ucanet```

2. Set a password that defies logic and reason  
```sudo passwd ucanet```

3. Move the ucanet.service file  
```sudo mv ucanet.service /etc/systemd/system/```

4. Reload the service files!  
```sudo systemctl daemon-reload```

5. Start the service, and check it's status  
```sudo systemctl start ucanet```  
```sudo systemctl status ucanet```

6. All good? Enable the service on every reboot  
```sudo systemctl enable ucanet```

## Python Requirements
Tested succesfully with Python 3.10.6  
**The package relies on the following modules:** (install with pip)  
requests, dnslib, tldextract, gitpython, apscheduler, cachetools

## Default Configuration (ucanet.ini)
Who doesn't love configuration files? Anyways ...

```
[DNS]
PORT=53
LISTEN=127.0.0.1

[WEB]
PORT=80
HOST=135.148.41.26
LOCAL=no

[LIB_REGISTRY]
PATH=./ucanet-registry/ucanet-registry.txt

[LIB_GIT]
USERNAME=Username
TOKEN=Token
URL=https://${USERNAME}:${PASSWORD}@github.com/ucanet/ucanet-registry.git
BRANCH=main
PATH=./ucanet-registry/

[LIB_CACHE]
TTL=600
SIZE=3500
```
Under DNS, we have the standard PORT set to 53 as well as the IP we want to LISTEN to, the LISTEN key should be set with *your* public facing IP.

Under WEB, there's a neocities handler, by default this is set to the official ucanet server IP.  
You can however serve neocities content yourself by setting LOCAL to yes and changing the HOST to your public facing IP... the port is by default 80 for the sake of simplicity, this document does not yet deal with setting it up behind apache / nginx or whatever web server you might otherwise have running already though.

The last three can pretty much be left alone unless you're running the Discord bot as well.
