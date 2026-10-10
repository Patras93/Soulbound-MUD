Option Explicit
' Soulbound: Windows Script Host launcher with no visible CMD window.
' The regular BAT and host_windows.py still collect logs and handle safe STOP.
Dim files, shell, gameFolder, batPath, exitCode
Set files = CreateObject("Scripting.FileSystemObject")
gameFolder = files.GetParentFolderName(WScript.ScriptFullName)
batPath = files.BuildPath(gameFolder, "Start-Soulbound-Windows.bat")
If Not files.FileExists(batPath) Then
    MsgBox "Brakuje Start-Soulbound-Windows.bat. Rozpakuj kompletna paczke Soulbound.", vbCritical, "Soulbound"
    WScript.Quit 2
End If
Set shell = CreateObject("WScript.Shell")
shell.CurrentDirectory = gameFolder
On Error Resume Next
exitCode = shell.Run(Chr(34) & batPath & Chr(34), 0, False)
If Err.Number <> 0 Then
    MsgBox "Nie udalo sie uruchomic Soulbound w tle: " & Err.Description, vbCritical, "Soulbound"
    WScript.Quit 3
End If
On Error GoTo 0
