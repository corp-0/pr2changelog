@echo off
set file=%1
cmd /k "act pull_request_target -e tests\data\%file%.json -W tests\pr2changelog_local.yml > log.log"
pause
exit