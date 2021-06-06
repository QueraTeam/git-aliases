#!/bin/bash

git config --local alias.qsubmit "! f() { SUBMIT_MSG=\$(head /dev/urandom | tr -dc a-z | head -c15); branches=\$(git for-each-ref --format '%(refname:short)' refs/heads); tags=\$(git tag -l); git push origin --atomic -f -q \$branches \$tags; git tag -a submit -m \"\$SUBMIT_MSG\" -f; git push origin submit -f; }; f"
