#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##########################################################
# title:  git-auto-deploy
# author: Josias Bruderer
# date:   29.07.2021
# desc:   updates files from github releases
##########################################################

import sys
from pathlib import Path
import traceback


project_path = Path.cwd().parent

# prepare to load project specific libraries
if project_path not in sys.path:
    sys.path.append(str(project_path))

# import modules
from modules import config_loader
from modules import git_api
from modules import sentry

try:
    # load config
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    else:
        config_file = 'config/default.json'

    sentryconfig = Path(config_file).parent.joinpath("sentry.txt")
    if sentryconfig.is_file() and len(sentryconfig.read_text()) > 0:
        sentry.sentry_init(sentryconfig.read_text())

    cfg = config_loader.Cfg(config_file)

    git = git_api.Git(cfg.config)
    git.updateAssets()
except Exception as e:
    print(traceback.format_exc())
    sentry.capture_exception(e)