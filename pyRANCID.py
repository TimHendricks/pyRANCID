#!/usr/bin/python
import smtplib
from  email.mime.text import MIMEText
import time
import pexpect
import difflib
import sys
from hashlib import sha512
import os
import pdb
 
def GetConfig(device,method,username,password):
     if method == 'telnet':
        p = pexpect.spawn('telnet ' + device)
        p.expect('Username:')
        p.sendline(username)
        p.expect('Password:')
        p.sendline(password)
        p.expect(device+'#')
        p.sendline('terminal length 0')
        p.expect(device+'#')
        p.sendline('show run')
        p.expect(device+'#')
        return p.before
     if device ==  'asa':
        p = pexpect.spawn('ssh '+ username + '@' + device)
        p.expect('password:')
        p.sendline(password)
        p.expect('asa-5520>')
        p.sendline('enable')
        p.expect('Password:')
        p.sendline(password)
        p.expect('asa-5520#')
        p.sendline('terminal pager 0')
        p.expect('asa-5520#')
        p.sendline('show run')
        p.expect('asa-5520#')
        return p.before
 
 
def ProcessDevice(device,method,username,password):
 
    newConfig = GetConfig(device,method,username,password)
 
    currentConfPath = "/home/pyRANCID/"+device+"-current.conf"
    if os.path.exists(currentConfPath):
        temp = open(currentConfPath,"r+")
    else:
        temp = open(currentConfPath,"w")
        temp.write(newConfig)
        temp.close()
        return
    currentConfig = temp.read()
    temp.close()
 
#stop if there are no changes
    if sha512(newConfig).hexdigest() == sha512(currentConfig).hexdigest():
        return
    changelogPath = "/home/pyRANCID/"+device+"-changelog"
    if os.path.exists(changelogPath):
        changelog = open("/home/pyRANCID/"+device+"-changelog","a")
    else:
        changelog = open("/home/pyRANCID/"+device+"-changelog","w")
    changes = []
for line in difflib.unified_diff(currentConfig.split("\r\n"),newConfig.split("\r\n")):
        changes.append(line)
    changes = '\n'.join(changes)
    changelog.write("==========================="+time.asctime()+"================\n")
    changelog.write(changes)
    changelog.close()
 
    os.rename("/home/pyRANCID/"+device+"-current.conf",device+"-"+str(time.strftime("%Y-%m-%d_%H:%M:%S")))
    current = open("/home/pyRANCID/"+device+"-current.conf","w+")
    current.write(newConfig)
    current.close()
 
    msg = MIMEText(changes)
    msg['Subject'] = "Changes to "+device+" have been made."
    msg['From'] ="pyRANCID"
    msg['To']   = "network-admins"
 
    s = smtplib.SMTP('mail.company.com')
    s.sendmail('pyRANCID@company.com','pyRANCID',msg.as_string())
    s.quit()
 
 
 
for line in open("/home/pyRANCID/router.db","r").readlines():
    line = line.strip()
    print line
    field = line.split(":")
    for i in field:
        print i
    if field[2]!='up':
        continue
    ProcessDevice(field[0],field[3],field[4],field[5])
