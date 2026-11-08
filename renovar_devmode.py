"""Renova sozinho o Developer Mode da TV. Roda pelo Agendador de Tarefas do Windows (pythonw: sem janela).

    pythonw -I renovar_devmode.py        # o que o agendador roda (de hora em hora, das 8h a meia-noite)
    python -I renovar_devmode.py --agora # renova mesmo que ja tenha renovado hoje, e mostra o resultado

Por que: o Developer Mode da LG vence em ~40 dias. Vencido, a TV apaga o Free My TV e o YouTube sem anuncios, e a
entrada "Free My TV" fica apontando para um app que nao existe mais. Renovar uma vez por dia sobra: depois de dar
certo, as outras tentativas do dia so saem (nem abrem conexao).
Como: acha a TV no cabo (achar_tv.py), le o token da sessao pela chave SSH ja salva e pede a renovacao ao servidor
oficial da LG (free-my-tv/webos/renew.py), depois pergunta a LG quanto tempo falta. TV desligada: nao faz nada e
tenta na proxima hora. O token e uma credencial: nunca vai para o log nem para a tela, e so viaja para a LG (https).
Cada tentativa fica em renovacao.log (ultimas 200 linhas).
"""
import datetime
import json
import os
import re
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'free-my-tv', 'webos'))

NO_WINDOW = 0x08000000   # CREATE_NO_WINDOW: o ssh que o renew.py chama nao abre janela (pythonw nao tem console)
_run = subprocess.run


def _quiet_run(*args, **kwargs):
    if os.name == 'nt':
        kwargs.setdefault('creationflags', NO_WINDOW)
    return _run(*args, **kwargs)


subprocess.run = _quiet_run   # antes de importar install/renew, que chamam subprocess.run

import achar_tv  # noqa: E402
import install  # noqa: E402
import renew  # noqa: E402

LOG = os.path.join(HERE, 'renovacao.log')
EVERY = datetime.timedelta(hours=20)   # uma renovacao por dia basta (a janela e de ~40 dias)
CHECK_HOST = 'https://developer.lge.com/secure/CheckDevModeSession.dev'


def log(message):
    line = '%s %s' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), message)
    lines = []
    if os.path.exists(LOG):
        with open(LOG, encoding='utf-8') as f:
            lines = f.read().splitlines()
    lines = (lines + [line])[-200:]
    with open(LOG, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    if sys.stdout:
        print(line)


def last_success():
    if not os.path.exists(LOG):
        return None
    with open(LOG, encoding='utf-8') as f:
        for line in reversed(f.read().splitlines()):
            if ' OK ' in line + ' ':
                try:
                    return datetime.datetime.strptime(line[:16], '%Y-%m-%d %H:%M')
                except ValueError:
                    return None
    return None


def time_left(ip):
    """Quanto falta, segundo a LG ('' se nao der para saber). Mesmo token, mesmo cuidado: sem redirecionamento."""
    try:
        token = renew.read_token(ip, install.saved_key(ip))
        if not re.fullmatch(r'[0-9a-fA-F]{32,128}', token):
            return ''
        url = CHECK_HOST + '?' + urllib.parse.urlencode({'sessionToken': token})
        with renew.urllib.request.build_opener(renew._NoRedirect).open(url, timeout=10) as r:
            body = json.loads(r.read().decode('utf-8', 'replace'))
        m = re.match(r'^(\d+):(\d+)', str(body.get('errorMsg', '')))
        return '%d dias e %d h' % divmod(int(m.group(1)), 24) if m else ''
    except (Exception, SystemExit):
        return ''


def main():
    forced = '--agora' in sys.argv
    last = last_success()
    if not forced and last and datetime.datetime.now() - last < EVERY:
        return 0   # ja renovado hoje: nem procura a TV
    ip = achar_tv.find_tv()
    if not ip:
        log('TV desligada ou fora do cabo: tento de novo na proxima hora.')
        return 1
    try:
        renew.renew(ip)   # imprime o sucesso, ou sai com o motivo (sys.exit)
    except SystemExit as e:
        log('FALHOU (%s): %s' % (ip, str(e.code).strip().replace('\n', ' ')[:300]))
        return 1
    left = time_left(ip)
    log('OK renovado (%s)%s' % (ip, ('; faltam %s' % left) if left else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
