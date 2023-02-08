"""
Script to create exe

How to use:
    make sure, icon.ico, arduino-cli, script.iss is exist and inno setup is installed

    In script.iss change:
        Line 23, LicenseFile
        Line 26, OutputDir
        Line 28, SetupIconFİle
        Line 41, Source
        Line 42, Source
    according to your path. also call4 variable in this file (Line 63) should be changed according to Line 26 (OutputDir).

    Then:

    Delete old build and dist files if exists
    run "python build.py"
    Inno setup will open, Run it with top left play button or by pressing F9. after it is completed close inno setup
    Press enter at command line to continue
    Windows will ask for certificate. confirm

    and you are done.
"""

import os
import shutil
import config


if os.path.exists('build') or os.path.exists('dist'):
    print("Delete Build And Dist Files!")
    exit()

os.system('pyinstaller --noconsole -i"icon.ico" main.py')
shutil.copy('icon.ico', 'dist/main/icon.ico')
shutil.copy('arduino-cli.exe', 'dist/main/arduino-cli.exe')
shutil.copy('dist/main/main.exe', 'dist/Deneyap Kart Web.exe')
os.remove('dist/main/main.exe')

newFile = ""
with open("script.iss", "r+") as buildISS:
    for line in buildISS:
        if ("MyAppVersion \"" in line):
            startIndex = line.find("\"")
            endIndex = line.rfind("\"")
            line = line.replace(line[startIndex + 1:endIndex], config.AGENT_VERSION)

        if ("OutputBaseFilename=DeneyapKartWebSetupv" in line):
            line = line.replace(line[39:], config.AGENT_VERSION) +"\n"
        newFile+=line

with open("script.iss", "w") as buildISS:
    buildISS.writelines(newFile)

os.system('script.iss')

input("Press Enter To Continue: ")

call1='$TestCodeSigningCert = New-SelfSignedCertificate -DnsName https://deneyapkart.org -Type CodeSigning -CertStoreLocation Cert:\CurrentUser\My'
call2='Export-Certificate -FilePath exported_cert.cer -Cert $TestCodeSigningCert'
call3='Import-Certificate -FilePath exported_cert.cer -CertStoreLocation Cert:\CurrentUser\Root'
call4=f'Set-AuthenticodeSignature -Certificate $TestCodeSigningCert -FilePath C:/Users/dc/Desktop/DeneyapKartWebSetupv{config.AGENT_VERSION}.exe'

os.system(f'C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe {call1} ; {call2} ; {call3} ; {call4}',)
