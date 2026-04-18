#!/bin/bash

TOKEN=$1

curl -k https://localhost/task \
-H "Authorization: Bearer $TOKEN"
