; PC Manager Lite - Inno Setup Script
; Requires Inno Setup 6.x

#define MyAppName "PC Manager Lite"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "PC Manager Lite"
#define MyAppURL "https://github.com/yourusername/pcmanager-lite"
#define MyAppExeName "PCManagerLite.exe"
#define MyAppDescription "Lightweight PC Management Utility"

; Root of the repo is one level up from this .iss file
#define RepoRoot RemoveBackslash(ExpandConstant('{#SourcePath}\..\'))

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Compression
Compression=lzma2/ultra64
SolidCompression=yes
; Visual
WizardStyle=modern
WizardResizable=no
; Output — absolute path so it always lands at repo root\installer_output\
OutputDir={#RepoRoot}installer_output
OutputBaseFilename=PCManagerLite_Setup_v{#MyAppVersion}
; Icon — absolute path relative to repo root
SetupIconFile={#RepoRoot}assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
; Privileges
PrivilegesRequired=admin
; Misc
DisableWelcomePage=no
DisableDirPage=no
DisableProgramGroupPage=yes
; Min Windows 10
MinVersion=10.0.17763

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startmenu";   Description: "Create Start Menu shortcut";   GroupDescription: "Shortcuts:"; Flags: checkedonce
Name: "autostart";   Description: "Start PC Manager Lite with Windows"; GroupDescription: "Startup:"; Flags: unchecked

[Files]
Source: "{#RepoRoot}dist\{#MyAppExeName}";  DestDir: "{app}"; Flags: ignoreversion
Source: "{#RepoRoot}assets\icon.ico";       DestDir: "{app}\assets"; Flags: ignoreversion
Source: "{#RepoRoot}assets\icon.png";       DestDir: "{app}\assets"; Flags: ignoreversion
Source: "{#RepoRoot}README.md";             DestDir: "{app}"; Flags: ignoreversion isreadme skipifsourcedoesntexist

[Icons]
Name: "{group}\{#MyAppName}";            Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icon.ico"
Name: "{group}\Uninstall {#MyAppName}";  Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}";      Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icon.ico"; Tasks: desktopicon

[Registry]
; Auto-start entry (only if task selected)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: string; ValueName: "{#MyAppName}"; \
  ValueData: """{app}\{#MyAppExeName}"""; \
  Flags: uninsdeletevalue; Tasks: autostart

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; \
  Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
