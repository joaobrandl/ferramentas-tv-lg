"""Records the TV's Timeline while Free My TV makes 6 moves along a row; prints time per record type.
Usage: profile.py IP [cards|shelf] [extra-css]"""
import base64, json, os, socket, struct, sys, time, urllib.request

ip = sys.argv[1]
zone = sys.argv[2] if len(sys.argv) > 2 else 'shelf'
css = sys.argv[3] if len(sys.argv) > 3 else None
pages = json.load(urllib.request.urlopen('http://%s:9998/json' % ip, timeout=5))
page = next(p for p in pages if 'io.freemytv' in p.get('url', ''))
path = page['webSocketDebuggerUrl'].split('9998', 1)[1]
s = socket.create_connection((ip, 9998), timeout=60)
s.sendall(('GET %s HTTP/1.1\r\nHost: %s:9998\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: %s\r\n'
           'Sec-WebSocket-Version: 13\r\n\r\n' % (path, ip, base64.b64encode(os.urandom(16)).decode())).encode())
buf = b''
while b'\r\n\r\n' not in buf:
    buf += s.recv(4096)
buf = buf.split(b'\r\n\r\n', 1)[1]


def send(obj):
    data = json.dumps(obj).encode(); mask = os.urandom(4); n = len(data)
    hdr = bytes([0x81]) + (bytes([0x80 | n]) if n < 126 else struct.pack('!BH', 0x80 | 126, n) if n < 65536 else struct.pack('!BQ', 0x80 | 127, n))
    s.sendall(hdr + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))


def exactly(n):
    global buf
    while len(buf) < n:
        c = s.recv(65536)
        if not c: raise OSError('closed')
        buf += c
    out, buf = buf[:n], buf[n:]
    return out


def recv():
    parts = b''
    while True:
        b1, b2 = exactly(2); n = b2 & 0x7f
        if n == 126: n = struct.unpack('!H', exactly(2))[0]
        elif n == 127: n = struct.unpack('!Q', exactly(8))[0]
        parts += exactly(n)
        if b1 & 0x80: return json.loads(parts.decode('utf-8', 'replace'))


ids = [0]
def call(method, params=None):
    ids[0] += 1
    send({'id': ids[0], 'method': method, 'params': params or {}})
    return ids[0]


if css is not None:
    call('Runtime.evaluate', {'expression': "var s=document.getElementById('exp')||document.createElement('style');s.id='exp';s.textContent=%s;document.head.appendChild(s);1" % json.dumps(css)})
setup = ("var F=FreeMyTV;for(var g=0;g<4&&F.state.zone!=='%s';g++){F.move(0,'%s'==='cards'?(F.state.zone==='top'?1:-1):1)}"
         "var __d=1,__n=0,__t=setInterval(function(){F.move(__d,0);if(++__n%%3===0)__d=-__d;if(__n>=6)clearInterval(__t)},400);1") % (zone, zone)
call('Timeline.start', {'maxCallStackDepth': 0})
time.sleep(0.5)
call('Runtime.evaluate', {'expression': setup})
records = []
end = time.time() + 3.6
s.settimeout(0.5)
while time.time() < end:
    try:
        m = recv()
    except socket.timeout:
        continue
    if m.get('method') == 'Timeline.eventRecorded':
        records.append(m['params']['record'])
s.settimeout(10)
call('Timeline.stop')
tot, cnt, mx = {}, {}, {}
def walk(r):
    t = r.get('type'); d = (r.get('endTime', r.get('startTime', 0)) - r.get('startTime', 0))
    tot[t] = tot.get(t, 0) + d; cnt[t] = cnt.get(t, 0) + 1; mx[t] = max(mx.get(t, 0), d)
    for c in r.get('children', []): walk(c)
for r in records: walk(r)
for t in sorted(tot, key=lambda k: -tot[k])[:14]:
    print('%-26s total %7.1f ms  n=%4d  max %6.1f ms' % (t, tot[t], cnt[t], mx[t]))
