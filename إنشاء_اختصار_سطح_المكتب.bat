@echo off
echo ========================================
echo    إنشاء اختصار DermaScan على سطح المكتب
echo ========================================
echo.

REM إنشاء اختصار على سطح المكتب
powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\DermaScan.lnk'); $Shortcut.TargetPath = '%~dp0dist\DermaScan.exe'; $Shortcut.WorkingDirectory = '%~dp0dist'; $Shortcut.Description = 'DermaScan - تطبيق تشخيص الأمراض الجلدية'; $Shortcut.IconLocation = '%~dp0static\img\logo.jpeg'; $Shortcut.Save()"

echo تم إنشاء الاختصار بنجاح على سطح المكتب!
echo يمكنك الآن النقر على الاختصار لتشغيل التطبيق.
echo.
pause 