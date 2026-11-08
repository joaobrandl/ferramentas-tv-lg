# Ferramentas para o Free My TV numa LG antiga (webOS 3)

Scripts de Windows que uso para manter o [Free My TV](https://github.com/simbasjungles/free-my-tv) numa LG 60UH6150
de 2016 (webOS 3.4), instalada pelo Developer Mode da LG, sem root. Ficam numa pasta ao lado do clone do Free My TV:

```
Projeto tv\
  free-my-tv\                  o app (clone do Free My TV, com as minhas mudanças na branch minha-tv-lg)
  ferramentas-tv\              esta pasta
  Fotos da tela de descanso\   uma subpasta por tema, com as fotos da tela de descanso
  Atualizar apps da TV.bat     atalho para ferramentas-tv\atualizar-apps.ps1
```

Precisa de Python 3, do OpenSSH do Windows e de a TV ter sido instalada uma vez com `free-my-tv\webos\install.py`
(que guarda a chave do Developer Mode em `%USERPROFILE%\.ssh`, nunca neste repositório).

| Arquivo | Para que serve |
|---|---|
| `atualizar-apps.ps1` | Um clique: lê os apps da TV, prepara as fotos, gera o app e instala na TV. |
| `preparar-fotos.ps1` | Converte as fotos (JPG, PNG, WEBP, HEIC) para 1920 x 1080, leves para a TV; pula arquivos estragados. |
| `achar_tv.py` | Acha a TV no cabo do PC (compartilhamento de internet do Windows), mesmo quando o IP dela muda. |
| `renovar_devmode.py` | Renova o Developer Mode da LG (vence em ~41 dias) pela tarefa agendada do Windows, quando a TV está no cabo. |
| `Desfazer inicio automatico.bat` | Remove a entrada "Free My TV" das entradas da TV (o "ligar já no app"). |
| `tvctl.py` | Uma chamada Luna, instalar ou remover um app de desenvolvedor pelo SSH do Developer Mode. |
| `tvjs.py`, `runbench.py`, `bench.js`, `profile.py` | Medem o app na TV pelo inspetor web do Developer Mode (fps, tempo do botão à tela). |

**Dados pessoais ficam fora:** o MAC da TV vai em `tv-mac.local.txt` (opcional; sem ele vale o aparelho que responder no
cabo), e o registro das renovações em `renovacao.log`, ambos ignorados pelo Git. Chaves, tokens e senhas nunca passam
por aqui.

O que aprendi nessa TV (webOS 3.4.3): o Chromium 38 dela não usa fontes variáveis; o instalador da LG descarta arquivos
cujas pastas não estão todas no pacote; apps de desenvolvedor não podem segurar a tela de descanso da LG; e registrar o
app como entrada da TV (para ligar direto nele) trava a TV depois de uma queda de luz — por isso foi desfeito.
