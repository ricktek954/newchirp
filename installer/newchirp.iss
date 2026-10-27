; NewChirp Windows installer (Inno Setup 6).
; Build with: ISCC.exe /DSourceDir=<release-bundle> /DMyAppVersion=1.0.0 installer\newchirp.iss

#ifndef MyAppName
  #define MyAppName "NewChirp"
#endif
#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif
#ifndef MyAppPublisher
  #define MyAppPublisher "com.rickext.newchirp"
#endif
#ifndef SourceDir
  #define SourceDir "..\build\windows\x64\runner\Release"
#endif
#ifndef InstallerOutputDir
  #define InstallerOutputDir "..\build"
#endif

[Setup]
AppId={{B01D9E7A-6C7D-45E8-9F3B-8C9A0C42E051}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL=https://newchirp.net
VersionInfoVersion={#MyAppVersion}.0
VersionInfoProductVersion={#MyAppVersion}
VersionInfoProductName={#MyAppName}
VersionInfoDescription={#MyAppName} Setup
VersionInfoCompany={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir={#InstallerOutputDir}
OutputBaseFilename=NewChirp-Installer-{#MyAppVersion}
SetupIconFile=..\windows\runner\resources\app_icon.ico
UninstallDisplayIcon={app}\newchirp.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion; Excludes: "*.pdb;*.exp;*.ilk;*.lib;*.obj"
Source: "..\assets\licenses\CHIRP-GPL-3.0.txt"; DestDir: "{app}\licenses"; Flags: ignoreversion
Source: "..\assets\licenses\PYSERIAL-BSD-3-CLAUSE.txt"; DestDir: "{app}\licenses"; Flags: ignoreversion
#ifdef VcRedistPath
Source: "{#VcRedistPath}"; DestDir: "{tmp}"; DestName: "vc_redist.x64.exe"
#endif

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\newchirp.exe"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\newchirp.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\newchirp.exe"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall runasoriginaluser; Check: ShouldLaunchAfterUpdate

[Code]
function ShouldLaunchAfterUpdate: Boolean;
begin
  Result := (not WizardSilent) or
    (ExpandConstant('{param:LAUNCHAPP|0}') = '1');
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    if FileExists(ExpandConstant('{tmp}\vc_redist.x64.exe')) then
    begin
      WizardForm.StatusLabel.Caption :='Installing Microsoft Visual C++ x64 runtime...';
      if Exec(ExpandConstant('{tmp}\vc_redist.x64.exe'),
          '/install /quiet /norestart', '', SW_HIDE,
          ewWaitUntilTerminated, ResultCode) then
        Log(Format('Microsoft VC++ redistributable returned code %d.', [ResultCode]))
      else
        Log('Could not launch the Microsoft VC++ redistributable.');
      WizardForm.StatusLabel.Caption := '';
    end;
  end;
end;
