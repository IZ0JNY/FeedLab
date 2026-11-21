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
AppPublisherURL=https://github.com/IZ0JNY/mwFeedDesign
AppSupportURL=https://github.com/IZ0JNY/mwFeedDesign/issues
DefaultDirName={localappdata}\Programs\FeedLab
DefaultGroupName=FeedLab
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist
OutputBaseFilename=FeedLab-Setup-{#MyAppVersion}
SetupIconFile=feedlab.ico
UninstallDisplayIcon={app}\python\FeedLab.exe
UninstallDisplayName=FeedLab {#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
CloseApplications=yes

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "openems"; Description: "Scarica e installa anche openEMS (facoltativo, ~100 MB: serve solo per la deep analysis full-wave; si può fare anche dopo, dall'app)"; GroupDescription: "Simulatore full-wave openEMS:"; Flags: unchecked

[InstallDelete]
Type: filesandordirs; Name: "{app}\app"

[Files]
Source: "..\build\FeedLab\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\FeedLab"; Filename: "{app}\python\FeedLab.exe"; Parameters: "-m feedlab.desktop"; WorkingDir: "{app}\app"; IconFilename: "{app}\feedlab.ico"; Comment: "Progettazione di feed/illuminatori a microonde"
Name: "{autoprograms}\FeedLab (nel browser)"; Filename: "{app}\python\FeedLab.exe"; Parameters: "-m feedlab.desktop --browser"; WorkingDir: "{app}\app"; IconFilename: "{app}\feedlab.ico"
Name: "{autodesktop}\FeedLab"; Filename: "{app}\python\FeedLab.exe"; Parameters: "-m feedlab.desktop"; WorkingDir: "{app}\app"; IconFilename: "{app}\feedlab.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\python\python.exe"; Parameters: "-u -m feedlab.openems_local install"; WorkingDir: "{app}\app"; StatusMsg: "Installazione di openEMS (download e prova)…"; Tasks: openems; Flags: waituntilterminated
Filename: "{app}\python\FeedLab.exe"; Parameters: "-m feedlab.desktop"; WorkingDir: "{app}\app"; Description: "Avvia FeedLab"; Flags: postinstall nowait skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\python"
Type: filesandordirs; Name: "{app}\app"
