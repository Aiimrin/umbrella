@echo off
schtasks /create /tn "EmailCheck" /tr "python E:\桌面\umbrella\check_feedback.py" /sc weekly /d MON /st 10:00 /f
echo Done
