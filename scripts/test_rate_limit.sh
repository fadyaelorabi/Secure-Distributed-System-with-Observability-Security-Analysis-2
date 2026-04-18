#!/bin/bash

TOKEN=$1

seq 1 50 | xargs -n1 -P20 curl -k https://localhost/task \
-H "Authorization: Bearer $TOKEN"

