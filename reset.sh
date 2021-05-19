#!/bin/bash

WATCHER_BRANCH=`head /dev/urandom | tr -dc a-z | head -c15`

git config credential.helper store

origin_url=`git remote get-url origin`

problem_id=`echo "$origin_url" | sed 's/.*\/p\-\([0-9]*\)\.git/\1/'`

ao_url=`echo "$origin_url" | sed 's/\(.*[/:]ao\-[0-9]*\/\).*/\1/'`
initial_remote_url=`echo "${ao_url}initial/initial-${problem_id}.git"`

git checkout --orphan $WATCHER_BRANCH
git reset --hard

submit_branches=`git for-each-ref --format '%(refname:short)' refs/heads`
while IFS= read -r branch; do
    git branch -D $branch
done <<< "$submit_branches"

initial_remote_name="initial_project"
git remote add $initial_remote_name $initial_remote_url

git fetch $initial_remote_name

remote_branches=`git for-each-ref --format '%(refname:short)' refs/remotes/${initial_remote_name}/`
while IFS= read -r branch; do
    fork_branch_name=`echo "$branch" | sed 's/[^/]*\/\(.*\)/\1/'`
    git checkout -b $fork_branch_name $branch
done <<< "$remote_branches"

git remote rm $initial_remote_name

branches=`git for-each-ref --format '%(refname:short)' refs/heads`

while IFS= read -r branch; do
    if [ "$branch" = "master" ]; then
        git checkout master
    elif [ "$branch" = "main" ]; then
        git checkout main
    fi
    break;
done <<< "$branches"

git push --all -f
git push --tags -f
