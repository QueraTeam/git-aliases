#!/bin/bash

SUBMIT_MSG=$(head /dev/urandom | tr -dc a-z | head -c15);

branches=$(git for-each-ref --format '%(refname:short)' refs/heads);
tags=$(git tag -l | grep -Ev '^submit.+$');

git tag -a submit -m "$SUBMIT_MSG" -f
git push origin --atomic -f -u -q $branches $tags;
