#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##########################################################
# title:  config_loader.py
# author: Josias Bruderer
# date:   28.07.2021
# desc:   loading config from a json file
##########################################################

import sys
import json


class Cfg:
    def __init__(self, cfg_file):
        self.cfg_file = cfg_file
        self.config = {}
        self.init()

    def init(self):
        try:
            with open(self.cfg_file) as config_file:
                self.config = json.load(config_file)
        except:
            print("Unexpected error: ", sys.exc_info()[0])
            raise
