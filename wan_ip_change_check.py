#!/usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------#
# DarkWolfCave.de  Tutorials und Snippets #
#                                         #
# Unifi WAN IP CHANGE Information         #
# Version 0.1 - only for private use      #
#-----------------------------------------#

import smtplib  # für Connection zu einem smtp-Server
from email.mime.text import MIMEText
import requests
import json
import urllib3
import paramiko # für ssh
import os
import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Zugänge zum unifi Gateway
gateway = {"ip": "192.168.1.36", "port": "8443"}  # deine IP und der genutzte Port
headers = {"Accept": "application/json", "Content-Type": "application/json"}
loginUrl = 'api/login'
url = f"https://{gateway['ip']}:{gateway['port']}/{loginUrl}"
auth = {"username": "UNIFI-Controller-USER", "password": "DEIN PASSWORT"}

def ssh_command(host_name, command):
    # Lese SSH-Konfiguration aus der .ssh/config-Datei
    ssh_config_file = os.path.expanduser('~/.ssh/config')  # Pfade können je nach System variieren
    ssh_config = paramiko.SSHConfig()
    ssh_config.parse(open(ssh_config_file))

    # Hole die Verbindungsinformationen für den angegebenen Host aus der Konfiguration
    host_config = ssh_config.lookup(host_name)

    # Stelle eine SSH-Verbindung her
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Verbinde dich mit den Informationen aus der Konfiguration
        ssh.connect(
            host_config['hostname'],
            username=host_config.get('user', None),
            port=int(host_config.get('port', 22)),  # Standard-Port, wenn nicht in der Konfiguration angegeben
            key_filename=host_config.get('identityfile', None)  # SSH-Schlüssel, wenn in der Konfiguration angegeben
        )

        # Befehl ausführen
        stdin, stdout, stderr = ssh.exec_command(command)

        # Befehlausgabe lesen
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')

        # Befehlausgabe ausgeben
        print('Befehlausgabe:')
        print(output)

        # Fehlerausgabe ausgeben
        if error:
            print('Fehler:')
            print(error)
    except Exception as e:
        print(f'Fehler bei der SSH-Verbindung: {str(e)}')
    finally:
        # SSH-Verbindung schließen, unabhängig vom Erfolg oder Fehler
        ssh.close()


session = requests.Session()
response = session.post(url, headers=headers, data=json.dumps(auth), verify=False)

# Überprüfe die erfolgreiche Anmeldung
if response.status_code != 200:
    print(f"Fehler bei der Anmeldung: {response.status_code}")
    exit()

# Rufe die WAN-IP-Adresse ab
wan_ip_url = f"https://{gateway['ip']}:{gateway['port']}/api/s/default/stat/health"
data = session.get(wan_ip_url).json()

if "wan_ip" in data["data"][1]:
    wan_ip = data["data"][1]["wan_ip"]
    print(f'Deine WAN-IP-Adresse ist: {wan_ip}')
# Lese die vorherige WAN-IP-Adresse aus der Textdatei
    try:
        # Versuche, die vorherige WAN-IP-Adresse aus der Textdatei zu lesen
        with open('wan_ip.txt', 'r') as file:
            previous_ip = file.read()
    except FileNotFoundError:
        # Wenn die Datei nicht gefunden wird, erstelle sie und speichere die aktuelle WAN-IP
        with open('wan_ip.txt', 'w') as file:
            file.write(wan_ip)
            print('Textdatei "wan_ip.txt" wurde erstellt.')
            previous_ip = wan_ip

    # Vergleiche die aktuelle WAN-IP mit der vorherigen WAN-IP
    if wan_ip == previous_ip:
        print("Die WAN-IP hat sich nicht geändert.")
    else:

        # Aktuelles Datum und Uhrzeit abrufen
        aktuelles_datum_uhrzeit = datetime.datetime.now()

        # Ausgabe des aktuellen Datum und Uhrzeit im gewünschten Format
        formatiertes_datum_uhrzeit = aktuelles_datum_uhrzeit.strftime("%d-%m-%Y %H:%M:%S")
        print("Aktuelles Datum und Uhrzeit:", formatiertes_datum_uhrzeit)
        print(f'Die WAN-IP hat sich geändert.\nAlte: {previous_ip}\nNeue: {wan_ip}\nAktualisiere die Textdatei und ändere .htaccess.')
        # Verbindung zum Server und Aufruf eines SH-Skripts
        # zum Ändern der IP in den .htaccess Dateien
        host_name = 'DER NAME IN DER .ssh/config Datei!'
        command_to_execute = '/PFAD zum anderen Skript/dwc-test.sh ' + wan_ip
        ssh_command(host_name, command_to_execute)

        server = smtplib.SMTP('smtp.DEIN-ANBIETER', 587)
        server.starttls()
        server.login("USERNAME", "PASSWORT")
        value = "Alte WAN IP: " + previous_ip+"\n \n Neue WAN IP: " + wan_ip
        msg = MIMEText(value)
        msg['Subject'] = "[WICHTIG!] NEUE WAN IP " + wan_ip
        msg['From'] = "DEINE EMAIL als Absender"
        msg['To'] = "EMAIL WOHIN gesendet werden soll"
        server.sendmail(msg['From'], msg['To'], msg.as_string())
        server.quit()
        # Aktualisiere die Textdatei mit der neuen WAN-IP
        with open('wan_ip.txt', 'w') as file:
            file.write(wan_ip)
else:
    print('WAN-IP-Adresse konnte nicht abgerufen werden.')

# Abmelden von der UniFi API
logout_url = f"https://{gateway['ip']}:{gateway['port']}/api/logout"
session.get(logout_url)