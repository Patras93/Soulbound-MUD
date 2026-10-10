Option Explicit
' Runs the short BAT invisibly and WAITS until CMD exits (no orphan launcher CMD).
Dim fs, shell, folder, bat, rc
Set fs = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")
folder = fs.GetParentFolderName(WScript.ScriptFullName)
bat = fs.BuildPath(folder, "Start-Soulbound-Windows.bat")
If Not fs.FileExists(bat) Then
    MsgBox "Brakuje Start-Soulbound-Windows.bat.", vbCritical, "Soulbound"
    WScript.Quit 2
End If
shell.CurrentDirectory = shell.ExpandEnvironmentStrings("%TEMP%")
On Error Resume Next
rc = shell.Run(Chr(34) & bat & Chr(34), 0, True)
If Err.Number <> 0 Then
    MsgBox "Blad startu Soulbound: " & Err.Description, vbCritical, "Soulbound"
    WScript.Quit 3
End If
On Error GoTo 0
If rc <> 0 Then
    MsgBox "Soulbound nie mogl zostac uruchomiony. Sprawdz logs\bledy.log.", vbCritical, "Soulbound"
End If
WScript.Quit rc
