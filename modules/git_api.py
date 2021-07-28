#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##########################################################
# title:  git_api.py
# author: Josias Bruderer
# date:   28.07.2021
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


class Git:
    def __init__(self, config):
        self.config = config
        self.baseURL = "https://api.github.com/repos/" + self.config["USERNAME"] + "/" + self.config["REPOSITORY"]
        self.releasePattern = re.compile(self.config["ASSETREGEX"])
        self.init()

    def init(self):
        print(self.baseURL)

    def getJSON(self, url):
        print(url)
        try:
            r = requests.get(url,
                             allow_redirects=True,
                             headers={"Accept":"application/vnd.github.v3+json",
                                      "Authorization": "token " + self.config["AUTHTOKEN"]})
            if r.status_code == 200:
                try:
                    return json.loads(r.content)
                except ValueError as err:
                    return False
            return r
        except:
            print("Unexpected error: ", sys.exc_info()[0])
            raise


    def getFILE(self, url):
        try:
            r = requests.get(url,
                             allow_redirects=True,
                             headers={"Accept": "application/octet-stream",
                                      "Authorization": "token " + self.config["AUTHTOKEN"]})
            if r.status_code == 200:
                return r.content
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
        releasesfiltered = list(filter(lambda x:x["prerelease"] == False, releases))
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
        if not destinationdir.is_dir():
            destinationdir.mkdir(parents=True, exist_ok=True)

        postscriptrun = False

        for a in assets:
            destination = Path(self.config["DESTINATIONDIR"] + "/" + a["name"])
            destinationnodeid = Path(self.config["DESTINATIONDIR"] + "/._" + a["name"] + ".node_id")

            if destination.is_file() and \
                    destination.stat().st_size == a["size"] and \
                    destinationnodeid.is_file() and \
                destinationnodeid.read_text() == a["node_id"]:
                warnings.warn("file with same size and node_id exists and will be skipped: " + str(destination.absolute()))
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

        return True