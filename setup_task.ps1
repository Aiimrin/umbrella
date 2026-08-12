$action = New-ScheduledTaskAction -Execute "python" -Argument "E:\桌面\umbrella\check_feedback.py"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "10:00AM"
Register-ScheduledTask -TaskName "EmailCheck" -Action $action -Trigger $trigger -Force
Get-ScheduledTask -TaskName EmailCheck | Format-List TaskName, State
