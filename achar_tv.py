"""Acha a TV LG no cabo do PC (compartilhamento de internet do Windows, rede 192.168.137.x) e escreve o IP dela.

    python achar_tv.py        # escreve o IP (saida 0) ou nada (saida 1, TV desligada ou fora do cabo)

O IP da TV muda quando ela reinicia de verdade (uma queda de luz trocou 192.168.137.193 por .228), entao os scripts
procuram pelo endereco fisico do cabo dela (MAC), que nao muda, em vez de um IP fixo. Primeiro os IPs que o Windows
ja associa a esse MAC, conferindo qual responde (a tabela guarda enderecos velhos); se nenhum responder (o PC
reiniciou, por exemplo), bate uma vez em cada endereco da rede do cabo e confere o MAC de quem respondeu.
So le: nao muda nada no PC nem na TV.
"""
import concurrent.futures
import re
import socket
import subprocess
import sys

import os


def _tv_mac():
    """O MAC do cabo da TV, de tv-mac.local.txt (ao lado deste arquivo, fora do Git) ou da variavel TV_MAC, no formato
    aa-bb-cc-dd-ee-ff (arp -a mostra assim). Sem ele, vale o primeiro aparelho que responder na rede do cabo
    (na pratica, so a TV esta ali)."""
    mac = os.environ.get('TV_MAC', '')
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tv-mac.local.txt')
    if not mac and os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            mac = f.read().strip()
    return mac.lower().replace(':', '-')


TV_MAC = _tv_mac()
NETWORK = '192.168.137.'       # a rede que o Windows cria no cabo ao compartilhar a internet
PORT = 3000                    # a API do controle remoto da LG: responde sempre que a TV esta ligada
NO_WINDOW = 0x08000000         # CREATE_NO_WINDOW: sem janela piscando quando roda pelo agendador


def answers(ip, timeout=0.8):
    try:
        with socket.create_connection((ip, PORT), timeout=timeout):
            return True
    except OSError:
        return False


def tv_addresses():
    """Os IPs que a tabela ARP do Windows associa ao MAC da TV (podem estar velhos)."""
    out = subprocess.run(['arp', '-a'], capture_output=True, text=True, creationflags=NO_WINDOW).stdout.lower()
    return [ip for ip, mac in re.findall(r'(\d+\.\d+\.\d+\.\d+)\s+([0-9a-f]{2}(?:-[0-9a-f]{2}){5})', out)
            if mac == TV_MAC and ip.startswith(NETWORK)]


def find_tv():
    for ip in tv_addresses():
        if answers(ip):
            return ip
    candidates = [NETWORK + str(n) for n in range(2, 255)]
    with concurrent.futures.ThreadPoolExecutor(64) as pool:
        hits = [ip for ip, ok in zip(candidates, pool.map(answers, candidates)) if ok]
    if not TV_MAC:
        return hits[0] if hits else None   # sem MAC configurado: quem respondeu na rede do cabo
    known = tv_addresses()   # a conexao acima poe o MAC de quem respondeu na tabela
    for ip in hits:
        if ip in known:
            return ip
    return None


if __name__ == '__main__':
    found = find_tv()
    if found:
        print(found)
    sys.exit(0 if found else 1)
