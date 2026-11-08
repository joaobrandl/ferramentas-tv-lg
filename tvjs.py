"""Evaluates JavaScript in Free My TV on the TV through its web inspector (port 9998). Usage: tvjs.py IP 'expr'"""
import base64, json, os, socket, struct, sys, urllib.request

ip, expr = sys.argv[1], sys.argv[2]
pages = json.load(urllib.request.urlopen('http://%s:9998/json' % ip, timeout=5))
page = next(p for p in pages if 'io.freemytv' in p.get('url', ''))
path = page['webSocketDebuggerUrl'].split('9998', 1)[1]

s = socket.create_connection((ip, 9998), timeout=60)
key = base64.b64encode(os.urandom(16)).decode()
s.sendall(('GET %s HTTP/1.1\r\nHost: %s:9998\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n'
           'Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n' % (path, ip, key)).encode())
buf = b''
while b'\r\n\r\n' not in buf:
    buf += s.recv(4096)
head, buf = buf.split(b'\r\n\r\n', 1)
assert b' 101 ' in head.split(b'\r\n')[0], head


def send(obj):
    data = json.dumps(obj).encode()
    mask = os.urandom(4)
    n = len(data)
    hdr = bytes([0x81]) + (bytes([0x80 | n]) if n < 126 else struct.pack('!BH', 0x80 | 126, n) if n < 65536
                           else struct.pack('!BQ', 0x80 | 127, n))
    s.sendall(hdr + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))


def exactly(n):
    global buf
    while len(buf) < n:
        chunk = s.recv(65536)
        if not chunk:
            raise OSError('closed')
        buf += chunk
    out, buf = buf[:n], buf[n:]
    return out


def recv():
    parts = b''
    while True:
        b1, b2 = exactly(2)
        n = b2 & 0x7f
        if n == 126:
            n = struct.unpack('!H', exactly(2))[0]
        elif n == 127:
            n = struct.unpack('!Q', exactly(8))[0]
        parts += exactly(n)
        if b1 & 0x80:
            return json.loads(parts.decode('utf-8'))


send({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}})
while True:
    m = recv()
    if m.get('id') == 1:
        r = m.get('result', {})
        res = r.get('result', {})
        print(json.dumps(res.get('value', res), ensure_ascii=False) if not r.get('wasThrown') else 'ERROR: ' + json.dumps(res, ensure_ascii=False))
        break
