#!/usr/bin/env python3
"""Daemonize the survey app - completely independent process"""
import os, sys, subprocess, time

BASE = '/share/home/zhaost/CP/IFPA'
LOG = os.path.join(BASE, 'survey_daemon.log')
PID = os.path.join(BASE, 'survey.pid')

# Kill any existing
if os.path.exists(PID):
    try:
        with open(PID) as f:
            old = int(f.read().strip())
        subprocess.run(['kill', str(old)], capture_output=True)
        time.sleep(1)
    except: pass

# Start with setsid to fully detach
proc = subprocess.Popen(
    [sys.executable, os.path.join(BASE, 'app.py')],
    cwd=BASE,
    stdout=open(LOG, 'w'),
    stderr=subprocess.STDOUT,
    stdin=subprocess.DEVNULL,
    start_new_session=True,   # This is key - creates a new process group
)

with open(PID, 'w') as f:
    f.write(str(proc.pid))

print(f'Started survey service (PID: {proc.pid})')
print(f'Log: {LOG}')

# Wait for it to be ready
time.sleep(3)
try:
    import urllib.request
    r = urllib.request.urlopen('http://127.0.0.1:8650/health', timeout=5)
    print(f'Health check: {r.status} OK')
except Exception as e:
    print(f'Warning: {e}')
    print('Check the log file for details')
