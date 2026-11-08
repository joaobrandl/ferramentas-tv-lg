"""Small helpers over Developer Mode SSH, reusing free-my-tv/webos/install.py (its saved key and luna-send-pub).

    python tvctl.py IP luna 'luna://service/method' '{"json":1}'   # one Luna call (public bus), prints the replies
    python tvctl.py IP install file.ipk app.id                      # installs an .ipk and opens it
    python tvctl.py IP remove app.id                                 # removes a Developer Mode app
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'free-my-tv', 'webos'))
import install  # noqa: E402  (free-my-tv's installer: ssh(), luna(), fetch_key())


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    ip, cmd = sys.argv[1], sys.argv[2]
    key = install.fetch_key(ip)
    if cmd == 'luna':
        print(install.luna(ip, key, sys.argv[3], json.loads(sys.argv[4]), replies=1, wait=15).strip())
    elif cmd == 'install':
        path, app_id = sys.argv[3], sys.argv[4]
        temp = '/media/developer/temp/tvctl.ipk'
        with open(path, 'rb') as f:
            data = f.read()
        print('Copying %s (%d KB) ...' % (os.path.basename(path), len(data) // 1024))
        copy = install.ssh(ip, key, 'mkdir -p /media/developer/temp && cat > ' + temp, data=data)
        if copy.returncode != 0:
            sys.exit('Copy failed: %r' % copy.stderr)
        print('Installing ...')
        out = install.luna(ip, key, 'luna://com.webos.appInstallService/dev/install',
                           {'id': app_id, 'ipkUrl': temp, 'subscribe': True}, replies=30, wait=90)
        install.ssh(ip, key, 'rm -f ' + temp)
        if '"state":"installed"' not in out:
            sys.exit('Not installed. The TV said:\n' + out.strip())
        install.luna(ip, key, 'luna://com.webos.applicationManager/launch', {'id': app_id})
        print('Installed and opened: ' + app_id)
    elif cmd == 'remove':
        out = install.luna(ip, key, 'luna://com.webos.appInstallService/dev/remove', {'id': sys.argv[3]}, replies=3, wait=30)
        print(out.strip())
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
