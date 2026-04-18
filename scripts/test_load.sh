#!/bin/bash

TOKEN=$1

for i in {1..10}; do
  curl -k https://localhost/task \
  -H "Authorization: Bearer $TOKEN"
done

