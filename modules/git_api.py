#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##########################################################
# title:  git_api.py
# author: Josias Bruderer
# date:   30.07.2021
# desc:   updates files from github releases
##########################################################

import sys
from pathlib import Path
import requests
import json
import warnings
import re
import zipfile
import subprocess
from jwcrypto import jwt
from jwcrypto import jwk
import time
import datetime
import string
import random
import os
import shutil


class Git:
    def __init__(self, config):
        self.config = config
        self.baseURL = "https://api.github.com/repos/" + self.config["USERNAME"] + "/" + self.config["REPOSITORY"]
        self.releasePattern = re.compile(self.config["ASSETREGEX"])
        self.gitAuth = ""
        self.gitAuthExpire = 0
        self.init()

    def init(self):
        self.getAuth()

    def getAuth(self):
        if self.gitAuth == "" or time.time() > self.gitAuthExpire:
            if "AUTHTOKEN" in self.config and len(self.config["AUTHTOKEN"]) > 0:
                self.gitAuth = "token " + self.config["AUTHTOKEN"]
                self.gitAuthExpire = time.time() + 3600
            if "PRIVATEKEY" in self.config and len(self.config["PRIVATEKEY"]) > 0 \
                    and "APPID" in self.config and len(str(self.config["APPID"])) > 1:
                pempath = Path(self.config["PRIVATEKEY"])

                if not pempath.is_file():
                    raise ValueError("Private Key not found in: " + str(pempath.absolute()))

                private_pem = pempath.read_bytes()
                private_key = jwk.JWK.from_pem(private_pem)

                self.gitAuthExpire = int(time.time()) + 270

                payload = {
                    # issued at time, 30 seconds in the past to allow for clock drift
                    "iat": int(time.time()) - 30,
                    # JWT expiration time (5 minute maximum)
                    "exp": self.gitAuthExpire + 30,
                    # GitHub App's identifier
                    "iss": self.config["APPID"]
                }

                jwtoken = jwt.JWT(header={"alg": "RS256"}, claims=payload)
                jwtoken.make_signed_token(private_key)
                self.gitAuth = "bearer " + jwtoken.serialize()

                r = self.getJSON("https://api.github.com/app/installations")
                installations = list(filter(lambda x: x["account"]["login"] == "chippmann", r))
                if len(installations) == 0:
                    raise ValueError("Authentication failure: no app installation suitable.")
                installationsid = installations[0]["id"]
                r = self.postJSON("https://api.github.com/app/installations/" + str(installationsid) + "/access_tokens")
                if "token" in r and len(r["token"]) > 0:
                    self.gitAuth = "token " + r["token"]
                    self.gitAuthExpire = datetime.datetime.strptime(r["expires_at"], "%Y-%m-%dT%H:%M:%S%z")
                else:
                    raise ValueError("Something did not work with generating authentication token...")

    def postJSON(self, url, d="", j=""):
        try:
            r = requests.post(url,
                              data=d,
                              json=j,
                              allow_redirects=True,
                              headers={"Accept": "application/vnd.github.v3+json",
                                       "Authorization": self.gitAuth})
            if 200 <= r.status_code < 300:
                try:
                    return json.loads(r.content)
                except ValueError as err:
                    return False
            else:
                raise ValueError("Status Code not 2XX for url " + url + " : " + str(r.status_code) + " " + r.text)
        except:
            print("Unexpected error: ", sys.exc_info()[0])
            raise

    def getJSON(self, url):
        try:
            r = requests.get(url,
                             allow_redirects=True,
                             headers={"Accept": "application/vnd.github.v3+json",
                                      "Authorization": self.gitAuth})
            if 200 <= r.status_code < 300:
                try:
                    return json.loads(r.content)
                except ValueError as err:
                    return False
            else:
                raise ValueError("Status Code not 2XX for url " + url + " : " + str(r.status_code) + " " + r.text)
        except:
            print("Unexpected error: ", sys.exc_info()[0])
            raise

    def getFILE(self, url):
        try:
            r = requests.get(url,
                             allow_redirects=True,
                             headers={"Accept": "application/octet-stream",
                                      "Authorization": self.gitAuth})
            if r.status_code == 200:
                return r.content
            else:
                raise ValueError("Status Code not 200: " + str(r.status_code) + " " + r.text)
        except:
            print("Unexpected error: ", sys.exc_info()[0])
            raise

    def searchName(self, data, pattern):
        if pattern.search(data):
            return True
        return False

    def getPublishedAt(self, data):
        return data.get('published_at')

    def updateAssets(self):
        releases = self.getJSON(self.baseURL + "/releases")
        releasesfiltered = list(filter(lambda x: not x["prerelease"] and not x["draft"], releases))
        releasesfiltered = list(filter(lambda x: self.searchName(x["name"], self.releasePattern), releasesfiltered))
        releasesfiltered.sort(key=self.getPublishedAt, reverse=True)

        if len(releasesfiltered) == 0:
            raise ValueError("No releases found in: " + self.baseURL + "\n" +
                             "Using Filter for name: " + self.releasePattern.pattern)

        assets = self.getJSON(releasesfiltered[0]["assets_url"])
        if len(assets) == 0:
            raise ValueError("No Assets found in: " + releasesfiltered[0]["assets_url"] + "\n" +
                             "Check: " + releasesfiltered[0]["html_url"])

        destinationdir = Path(self.config["DESTINATIONDIR"])
        randomstr = "tmp_" + "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
        tmpdir = Path(destinationdir, randomstr)
        if not destinationdir.is_dir():
            destinationdir.mkdir(parents=True, exist_ok=True)

        if not tmpdir.is_dir():
            tmpdir.mkdir(parents=True, exist_ok=True)

        for f in os.listdir(destinationdir):
            if not f == randomstr:
                os.rename(Path(destinationdir, f), Path(tmpdir, f))

        postscriptrun = False

        for a in assets:
            destination = Path(destinationdir, a["name"])
            destinationtmp = Path(tmpdir, a["name"])
            destinationnodeid = Path(destinationdir, str("._" + a["name"] + ".node_id"))
            destinationnodeidtmp = Path(tmpdir, str("._" + a["name"] + ".node_id"))

            if destinationtmp.is_file() and \
                    destinationtmp.stat().st_size == a["size"] and \
                    destinationnodeidtmp.is_file() and \
                    destinationnodeidtmp.read_text() == a["node_id"]:
                warnings.warn("file with same size and node_id exists and will be skipped: " \
                              + str(destination.absolute()))
                os.rename(destinationtmp, destination)
                os.rename(destinationnodeidtmp, destinationnodeid)
                if self.config["UNZIPDIR"] != "" \
                        and Path(self.config["UNZIPDIR"]) == destinationdir \
                        and zipfile.is_zipfile(str(destination)):
                    with zipfile.ZipFile(str(destination), 'r') as zip_ref:
                        zip_ref.extractall(self.config["UNZIPDIR"])
            else:
                asset = self.getFILE(a["url"])
                if len(asset) > 0:
                    destination.write_bytes(asset)
                    destinationnodeid.write_text(a["node_id"])
                    if self.config["UNZIPDIR"] != "" and zipfile.is_zipfile(str(destination)):
                        with zipfile.ZipFile(str(destination), 'r') as zip_ref:
                            zip_ref.extractall(self.config["UNZIPDIR"])
                    postscriptrun = True
                else:
                    raise ValueError("No bytes recieved for: " + a["url"])

        if postscriptrun:
            if self.config["POSTSCRIPT"] != "":
                rc = subprocess.call(self.config["POSTSCRIPT"])

        shutil.rmtree(tmpdir)

        return True