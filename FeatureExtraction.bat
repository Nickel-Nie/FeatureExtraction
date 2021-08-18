@echo off
chcp 65001
set PWD=%~sdp0

python %PWD%\ModuleTest.py -i "%~1" -r [200:300]+[100:200] -m 20 -n 32 -x 2
pause