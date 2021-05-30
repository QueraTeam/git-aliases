"! f() { WATCHER_BRANCH=\$(head /dev/urandom | tr -dc a-z | head -c15); git config credential.helper store; origin_url=\$(git remote get-url origin); if [ -z \"\$1\" ]; then problem_id=\$(echo \"\$origin_url\" | sed 's/.*\/p\-\([0-9]*\)\.git/\1/'); ao_url=\$(echo \"\$origin_url\" | sed 's/\(.*[/:]ao\-[0-9]*\/\).*/\1/'); initial_remote_url=\$(echo \"\${ao_url}initial/initial-\${problem_id}.git\"); else initial_remote_url=\"\$1\"; fi; git merge --quit; rm -rf \".git/rebase-apply\"; git checkout --orphan \$WATCHER_BRANCH -q; git remote rm origin; git reset --hard -q; local_branches=\$(git for-each-ref --format '%(refname:short)' refs/heads); for branch in \"\$local_branches\"; do git branch -D \$branch -q; done; git remote add origin \$origin_url; git fetch origin -q; submit_remote_branches=\$(git for-each-ref --format '%(refname:short)' refs/remotes/origin); for branch in \"\$submit_remote_branches\"; do remote_name=\$(echo \$branch | cut -d'/' -f1); branch_name=\$(echo \$branch | sed 's/[^/]*\/\(.*\)/\1/'); if [ \"\$branch_name\" != \"master\" ] && [ \"\$branch_name\" != \"main\" ]; then git push --delete \$remote_name \$branch_name -q > /dev/null; fi; done; initial_remote_name=\$(head /dev/urandom | tr -dc a-z | head -c15); git remote add \$initial_remote_name \$initial_remote_url; git fetch \$initial_remote_name -q; initial_remote_branches=\$(git for-each-ref --format '%(refname:short)' refs/remotes/\${initial_remote_name}/); for branch in \"\$initial_remote_branches\"; do fork_branch_name=\$(echo \"\$branch\" | sed 's/[^/]*\/\(.*\)/\1/'); git checkout -b \$fork_branch_name \$branch -q; done; local_tags=\$(git tag -l); for tag in \"\$local_tags\"; do git tag --delete \$tag; done; git fetch origin --tags -f -q; remote_tags=\$(git tag -l); for tag in \"\$remote_tags\"; do git tag --delete \$tag > /dev/null; if [[ \$tag != submit* ]]; then git push -f --delete origin \$tag -q > /dev/null; fi; done; git fetch \$initial_remote_name --tags -q; remotes=\$(git remote); for remote in \"\$remotes\"; do if [ \"\$remote\" != \"origin\" ]; then git remote rm \$remote; fi; done; branches=\$(git for-each-ref --format '%(refname:short)' refs/heads); for branch in \"\$branches\"; do if [ \"\$branch\" = \"master\" ]; then git checkout master -q; break; elif [ \"\$branch\" = \"main\" ]; then git checkout main -q; break; fi; done; git push --all -f -q; git push --tags -f -q; echo \"Your repo have been reset to the initial state.\" }; f"