#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##########################################################
# title:  generate_authtoken.py
# author: Josias Bruderer
# date:   29.07.2021
# desc:   generates an authtoken
##########################################################

import sys
from pathlib import Path
from OpenSSL import crypto
from jwcrypto import jwt, jwk
import time
import requests


if len(sys.argv) > 1:
    pempath = Path(sys.argv[1])


if not pempath.is_file():
    raise ValueError("Private Key not found in: " + str(pempath.absolute()))

private_pem = pempath.read_bytes()
private_key = jwk.JWK.from_pem(private_pem)

payload = {
  # issued at time, 60 seconds in the past to allow for clock drift
  "iat": time.time() - 60,
  # JWT expiration time (5 minute maximum)
  "exp": time.time() + (300),
  # GitHub App's identifier
  "iss": 129110
}

jwt = jwt.JWT(header={"alg": "RS256"}, claims=payload)
jwt.make_signed_token(private_key)

try:
    r = requests.get("https://api.github.com/app",
                     allow_redirects=True,
                     headers={"Accept": "application/vnd.github.v3+json",
                              "Authorization": "Bearer " + jwt.serialize()})
    if r.status_code == 200:
        print("success")
    else:
        print("failed:" + r.text)
except:
    print("Unexpected error: ", sys.exc_info()[0])
    raise