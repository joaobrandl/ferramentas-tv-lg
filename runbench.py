"""Runs bench.js on the TV through tvjs.py and prints the result. Usage: runbench.py IP"""
import os, subprocess, sys, time

here = os.path.dirname(os.path.abspath(__file__))
ip = sys.argv[1]
js = open(os.path.join(here, 'bench.js'), encoding='utf-8').read()


def ev(expr):
    return subprocess.run([sys.executable, '-I', os.path.join(here, 'tvjs.py'), ip, expr],
                          capture_output=True, text=True, timeout=90).stdout.strip()


print(ev(js))
time.sleep(11)
print(ev('JSON.stringify(window.__bench)'))
