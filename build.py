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
call4=f'Set-AuthenticodeSignature -Certificate $TestCodeSigningCert -FilePath C:/Users/Kinkintama/Desktop/Deneyap/DeneyapKartSetup/DeneyapKartWebSetupv{config.AGENT_VERSION}.exe'

os.system(f'C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe {call1} ; {call2} ; {call3} ; {call4}',)
