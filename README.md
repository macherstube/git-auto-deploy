# Git Auto Deploy

This tool helps to automatically deploy stuff from Github to a server. \
This simplifies the deployment of configuration and application updates.

## Usage

Using an executable from releases:

### Option: App Authentication

1. Create an Github app under \
   https://github.com/settings/developers \
   or \
   https://github.com/organizations/[ORGANIZATION]/settings/apps
2. Set Repository permissions for "Contents" to "Access: Read-only"
3. Install App to required Repositories (in menu: Install App)
4. Create Private Key and save *.pem to your computer (in menu: General)
5. Create a config file f.E. config/default.json (see config/example.json)
6. To use Sentry add a file called sentry.txt at the same place as config file (f.E. config/sentry.txt)
7. Run:

./git-auto-deploy /path/to/config.json

### Option: Token Authentication (not recommended)

1. Create a token under https://github.com/settings/tokens/new with scope: "repo"
2. Create a config file f.E. config/default.json (see config/example.json)
3. To use Sentry add a file called sentry.txt at the same place as config file (f.E. config/sentry.txt)
4. Run:

./git-auto-deploy /path/to/config.json

## install as a service

The following lines of code helps to install git-auto-deploy as a cronjob (adapt that for windows of osx)

```bash
sudo mkdir /opt/git-auto-deploy
cd /opt/git-auto-deploy
sudo wget https://github.com/macherstube/git-auto-deploy/releases/download/v0.0.11/git-auto-deploy_linux -O git-auto-deploy_linux
sudo chmod 770 git-auto-deploy_linux
echo $'#!/bin/bash\n\n' | sudo tee postscript.sh > /dev/null
sudo chmod 770 postscript.sh

sudo mkdir /etc/git-auto-deploy
cd /etc/git-auto-deploy
echo $'{\n  "USERNAME": "",\n  "REPOSITORY": "",\n  "PRIVATEKEY": "/etc/git-auto-deploy/default.pem",\n  "APPID": 0,\n  "AUTHTOKEN": "",\n  "ASSETREGEX": "",\n  "DESTINATIONDIR": "",\n  "UNZIPDIR": "",\n  "POSTSCRIPT": "/opt/git-auto-deploy/postscript.sh"\n}' | sudo tee default.json > /dev/null
sudo chmod 600 default.json
sudo cp /path/to/downloaded/private-key.pem /etc/git-auto-deploy/default.pem
sudo chmod 400 default.pem

sudo nano /etc/git-auto-deploy/default.json
sudo nano /opt/git-auto-deploy/postscript.sh

sudo crontab -l > /tmp/cron_backup
sudo echo "*/5 * * * * /opt/git-auto-deploy/git-auto-deploy_linux /etc/git-auto-deploy/default.json" >> /tmp/cron_backup
sudo crontab /tmp/cron_backup
sudo rm /tmp/cron_backup
```

