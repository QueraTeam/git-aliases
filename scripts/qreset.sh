#!/bin/bash

WATCHER_BRANCH=$(head /dev/urandom | tr -dc a-z | head -c15)

git config credential.helper store

origin_url=$(git remote get-url origin)

if [ -z "$1" ]; then
  problem_id=$(echo "$origin_url" | sed 's/.*\/p\-\([0-9]*\)\.git/\1/')
  ao_url=$(echo "$origin_url" | sed 's/\(.*[/:]ao\-[0-9]*\/\).*/\1/')
  initial_remote_url=$(echo "${ao_url}initial/initial-${problem_id}.git")
else
  initial_remote_url="$1"
fi

git checkout --orphan $WATCHER_BRANCH -q
git reset --hard -q

submit_branches=$(git for-each-ref --format '%(refname:short)' refs/heads)
while IFS= read -r branch; do
  git branch -D $branch -q
done <<<"$submit_branches"

initial_remote_name=$(head /dev/urandom | tr -dc a-z | head -c15)
git remote add $initial_remote_name $initial_remote_url
git fetch $initial_remote_name -q

remote_branches=$(git for-each-ref --format '%(refname:short)' refs/remotes/${initial_remote_name}/)
while IFS= read -r branch; do
  fork_branch_name=$(echo "$branch" | sed 's/[^/]*\/\(.*\)/\1/')
  git checkout -b $fork_branch_name $branch -q
done <<<"$remote_branches"

local_tags=$(git tag -l)
while IFS= read -r tag; do
  git tag --delete $tag
done <<<"$local_tags"
git fetch origin --tags -f -q
remote_tags=$(git tag -l)
while IFS= read -r tag; do
  if [[ $tag != submit* ]]; then
    git tag --delete $tag
    git push -f --delete origin $tag -q
  fi
done <<<"$remote_tags"
git fetch $initial_remote_name --tags -q

remotes=$(git remote)
while IFS= read -r remote; do
  if [ "$remote" != "origin" ]; then
    git remote rm $remote
  fi
done <<<"$remotes"

branches=$(git for-each-ref --format '%(refname:short)' refs/heads)
while IFS= read -r branch; do
  if [ "$branch" = "master" ]; then
    git checkout master -q
    break
  elif [ "$branch" = "main" ]; then
    git checkout main -q
    break
  fi
done <<<"$branches"

git push --all -f -q
git push --tags -f -q

echo "Your repo have been reset to the initial state."
