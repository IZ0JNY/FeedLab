; FeedLab installer (Inno Setup 6). Built by windows\build.ps1 from build\FeedLab.
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif

[Setup]
AppId={{6E3F2A41-9B0C-4E5D-A7C2-2F1E0D5B8C47}
AppName=FeedLab
AppVersion={#MyAppVersion}
AppVerName=FeedLab {#MyAppVersion}
AppPublisher=IZ0JNY
AppPublisherURL=https://github.com/IZ0JNY/FeedLab
AppSupportURL=https://github.com/IZ0JNY/FeedLab/issues
DefaultDirName={localappdata}\Programs\FeedLab
DefaultGroupName=FeedLab
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist
OutputBaseFilename=FeedLab-Setup-{#MyAppVersion}
SetupIconFile=feedlab.ico
UninstallDisplayIcon={app}\feedlab.ico
UninstallDisplayName=FeedLab {#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
CloseApplications=yes
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany=IZ0JNY
VersionInfoDescription=FeedLab setup - microwave feed design
VersionInfoProductName=FeedLab
VersionInfoProductVersion={#MyAppVersion}
VersionInfoCopyright=(c) Ivan De Cesaris IZ0JNY - GPLv3
LicenseFile=..\LICENSE

ShowLanguageDialog=yes
UsePreviousLanguage=no

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
italian.AppComment=Progettazione di feed/illuminatori a microonde
english.AppComment=Microwave feed/illuminator design
italian.InBrowser=nel browser
english.InBrowser=in the browser
italian.OldAllUsers=È installata anche una copia di FeedLab per tutti gli utenti: per rimuoverla (e togliere la sua icona) usa Impostazioni > App > FeedLab > Disinstalla.
english.OldAllUsers=A copy of FeedLab installed for all users is also present: to remove it (and its icon) use Settings > Apps > FeedLab > Uninstall.

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Registry]
; language chosen in the installer = default language of the app (changeable in the app sidebar)
Root: HKCU; Subkey: "Software\FeedLab"; ValueType: string; ValueName: "Language"; ValueData: "{language}"; Flags: uninsdeletekey

[InstallDelete]
Type: filesandordirs; Name: "{app}\app"
; clean upgrade: no packages left over from the previous version
Type: filesandordirs; Name: "{app}\python"
; Start-menu entry "in the browser" of a previous install in the other language (recreated below)
Type: files; Name: "{autoprograms}\FeedLab (nel browser).lnk"
Type: files; Name: "{autoprograms}\FeedLab (in the browser).lnk"
; launcher of versions up to 0.4.10 (modified copy of pythonw.exe): no longer used
Type: files; Name: "{app}\python\FeedLab.exe"

[Files]
Source: "..\build\FeedLab\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\FeedLab"; Filename: "{app}\python\pythonw.exe"; Parameters: "-m feedlab.desktop"; WorkingDir: "{app}\app"; IconFilename: "{app}\feedlab.ico"; AppUserModelID: "IZ0JNY.FeedLab"; Comment: "{cm:AppComment}"
Name: "{autoprograms}\FeedLab ({cm:InBrowser})"; Filename: "{app}\python\pythonw.exe"; Parameters: "-m feedlab.desktop --browser"; WorkingDir: "{app}\app"; IconFilename: "{app}\feedlab.ico"; AppUserModelID: "IZ0JNY.FeedLab"
Name: "{autodesktop}\FeedLab"; Filename: "{app}\python\pythonw.exe"; Parameters: "-m feedlab.desktop"; WorkingDir: "{app}\app"; IconFilename: "{app}\feedlab.ico"; AppUserModelID: "IZ0JNY.FeedLab"; Tasks: desktopicon

[Run]
Filename: "{app}\python\pythonw.exe"; Parameters: "-m feedlab.desktop"; WorkingDir: "{app}\app"; Description: "{cm:LaunchProgram,FeedLab}"; Flags: postinstall nowait skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\python"
Type: filesandordirs; Name: "{app}\app"

[Code]
// Remove any previous FeedLab first (per-user or for all users), with its icons and Programs entry,
// so that after an update there is only one FeedLab and one set of shortcuts. Simulations and settings
// (Documents\FeedLab, openEMS) are outside the program folder and stay.
const
  UninstKey = 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{6E3F2A41-9B0C-4E5D-A7C2-2F1E0D5B8C47}_is1';

procedure UninstallPrevious(RootKey: Integer);
var
  Cmd: String;
  Code: Integer;
begin
  if RegQueryStringValue(RootKey, UninstKey, 'UninstallString', Cmd) then
  begin
    Cmd := RemoveQuotes(Cmd);
    if FileExists(Cmd) then
      Exec(Cmd, '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART', '', SW_HIDE, ewWaitUntilTerminated, Code);
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
  begin
    UninstallPrevious(HKCU);
    if IsAdminInstallMode then
      UninstallPrevious(HKLM)
    else if RegKeyExists(HKLM, UninstKey) then
      // a copy installed for all users needs administrator rights to be removed: leave it and say so
      MsgBox(CustomMessage('OldAllUsers'), mbInformation, MB_OK);
  end;
end;

