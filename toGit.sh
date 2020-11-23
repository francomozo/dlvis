#!/bin/sh
# Usage: inside the git project pushes all with an obs string
# 'bash toGit.sh [OPTIONAL] "Message for the push" '

echo "---------- Capturing date and time ---------------------"
datetime=$(date '+%d/%m/%Y %H:%M');

echo "-------------- Git pulling -----------------------------"
git pull origin master

echo "--------------- Adding all -----------------------------"
git add --all

echo "-------------- Making commit ---------------------------"
obs="$1"
git commit -m "$datetime $obs"

echo "------------ Pushing to server -------------------------"
git push -u origin master

echo "------------ Done --------------------------------------"
