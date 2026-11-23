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

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Registry]
; language chosen in the installer = default language of the app (changeable in the app sidebar)
Root: HKCU; Subkey: "Software\FeedLab"; ValueType: string; ValueName: "Language"; ValueData: "{language}"; Flags: uninsdeletekey

[InstallDelete]
Type: filesandordirs; Name: "{app}\app"
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
