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

ShowLanguageDialog=yes
UsePreviousLanguage=no

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[CustomMessages]
italian.OemsTask=Scarica e installa anche openEMS (facoltativo, ~100 MB: serve solo per la deep analysis full-wave; si può fare anche dopo, dall'app)
english.OemsTask=Also download and install openEMS (optional, ~100 MB: only needed for the full-wave deep analysis; can also be done later from the app)
german.OemsTask=openEMS ebenfalls herunterladen und installieren (optional, ~100 MB: nur für die Full-wave-Tiefenanalyse; auch später in der App möglich)
french.OemsTask=Télécharger et installer aussi openEMS (facultatif, ~100 Mo : seulement pour l'analyse approfondie full-wave ; possible plus tard depuis l'application)
spanish.OemsTask=Descargar e instalar también openEMS (opcional, ~100 MB: solo para el análisis profundo full-wave; también se puede hacer después desde la aplicación)
italian.OemsGroup=Simulatore full-wave openEMS:
english.OemsGroup=openEMS full-wave simulator:
german.OemsGroup=Full-wave-Simulator openEMS:
french.OemsGroup=Simulateur full-wave openEMS :
spanish.OemsGroup=Simulador full-wave openEMS:
italian.OemsStatus=Installazione di openEMS (download e prova)…
english.OemsStatus=Installing openEMS (download and test)…
german.OemsStatus=openEMS wird installiert (Download und Test)…
french.OemsStatus=Installation d'openEMS (téléchargement et test)…
spanish.OemsStatus=Instalando openEMS (descarga y prueba)…
italian.AppComment=Progettazione di feed/illuminatori a microonde
english.AppComment=Microwave feed/illuminator design
german.AppComment=Entwurf von Mikrowellen-Speisesystemen
french.AppComment=Conception de sources/illuminateurs hyperfréquences
spanish.AppComment=Diseño de alimentadores/iluminadores de microondas
italian.InBrowser=nel browser
english.InBrowser=in the browser
german.InBrowser=im Browser
french.InBrowser=dans le navigateur
spanish.InBrowser=en el navegador

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "openems"; Description: "{cm:OemsTask}"; GroupDescription: "{cm:OemsGroup}"; Flags: unchecked

[Registry]
; language chosen in the installer = default language of the app (changeable in the app sidebar)
Root: HKCU; Subkey: "Software\FeedLab"; ValueType: string; ValueName: "Language"; ValueData: "{language}"; Flags: uninsdeletekey

[InstallDelete]
Type: filesandordirs; Name: "{app}\app"

[Files]
Source: "..\build\FeedLab\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\FeedLab"; Filename: "{app}\python\FeedLab.exe"; Parameters: "-m feedlab.desktop"; WorkingDir: "{app}\app"; IconFilename: "{app}\feedlab.ico"; Comment: "{cm:AppComment}"
Name: "{autoprograms}\FeedLab ({cm:InBrowser})"; Filename: "{app}\python\FeedLab.exe"; Parameters: "-m feedlab.desktop --browser"; WorkingDir: "{app}\app"; IconFilename: "{app}\feedlab.ico"
Name: "{autodesktop}\FeedLab"; Filename: "{app}\python\FeedLab.exe"; Parameters: "-m feedlab.desktop"; WorkingDir: "{app}\app"; IconFilename: "{app}\feedlab.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\python\python.exe"; Parameters: "-u -m feedlab.openems_local install"; WorkingDir: "{app}\app"; StatusMsg: "{cm:OemsStatus}"; Tasks: openems; Flags: waituntilterminated
Filename: "{app}\python\FeedLab.exe"; Parameters: "-m feedlab.desktop"; WorkingDir: "{app}\app"; Description: "{cm:LaunchProgram,FeedLab}"; Flags: postinstall nowait skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\python"
Type: filesandordirs; Name: "{app}\app"
