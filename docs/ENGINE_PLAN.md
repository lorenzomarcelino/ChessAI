# Plano de construção da engine de xadrez

Documento de planejamento da IA própria do ChessAI. Não usar Stockfish, Leela Chess Zero nem LLM como oponente. A engine é **busca escrita por nós** + **rede treinada por nós**.

Nível-alvo realista em PC de casa: clube (~1500–2000 Elo). Stockfish (~3500) está fora de escopo.

---

## Princípios

1. A UI Pygame (`src/`) não entra na busca. A engine vive em `engine/` e fala por FEN / lance UCI.
2. Sem busca, a rede sozinha joga mal. Fase 1 vem antes do treino.
3. Um modelo forte + limitadores de skill. Não treinar uma rede por dificuldade no início.
4. Cada fase só começa quando a anterior tem os arquivos e os critérios de pronto abaixo.

---

## Arquitetura-alvo (fim da Fase 5)

```
posição (FEN)
    → policy da rede (ordena lances)
    → alpha-beta / iterative deepening
    → value da rede (folha da árvore)
    → skill.py aplica teto de nós / ruído / sorteio
    → lance UCI para o Pygame
```

Stack: Python, `python-chess`, PyTorch, NumPy (Numba/Cython depois, se a busca ficar lenta).

---

## Mapa das fases

| Fase | Nome | Entrega |
| --- | --- | --- |
| 0 | Núcleo rápido | Tabuleiro legal, sem Pygame, testado |
| 1 | Engine clássica | Alpha-beta + eval artesanal, já joga |
| 2 | Rede | CNN value+policy, pesos nossos |
| 3 | Treino | PGN → destilação → self-play |
| 4 | Rede na busca | Eval da rede substitui material+PST |
| 5 | Dificuldades | Iniciante → Mestre no menu |
| 6 | Integração | Vs computador no Pygame |

---

## Estrutura final do repositório

```
ChessAI/
├── src/                      # jogo atual (Pygame)
├── engine/                   # núcleo da IA (sem Pygame)
│   ├── __init__.py
│   ├── board.py              # wrapper python-chess: push/pop/FEN
│   ├── search.py             # negamax, alpha-beta, ID, TT, quiescência
│   ├── evaluate.py           # eval artesanal (Fase 1) + ponte para a rede
│   ├── network.py            # arquitetura PyTorch
│   ├── encode.py             # posição → tensores 8×8×N
│   ├── skill.py              # níveis de dificuldade
│   ├── time_manager.py       # quanto tempo gastar no lance
│   └── api.py                # think(fen, skill, time_ms) → uci
├── train/
│   ├── dataset.py            # PGN → posições rotuladas
│   ├── train.py              # loop de treino
│   ├── distill.py            # relabel com a própria busca
│   ├── selfplay.py           # partidas engine vs engine
│   └── eval_match.py         # v1 vs v2, skill alto vs baixo
├── models/                   # checkpoints .pt (não commitar binários grandes)
├── tests/
│   ├── test_board.py
│   ├── test_search.py
│   └── test_encode.py
└── docs/
    └── ENGINE_PLAN.md
```

Nas fases 0–1 ainda **não** existem `network.py`, `train/` nem `models/`.

---

## Fase 0 — Núcleo rápido

Objetivo: regras corretas e rápidas, desligadas da UI.

### Arquivos que devem existir

```
engine/__init__.py
engine/board.py
tests/test_board.py
```

`engine/board.py` precisa expor:

- `from_fen` / `to_fen`
- `legal_moves()` (lista UCI)
- `push(uci)` / `pop()`
- `turn`, `is_checkmate`, `is_stalemate`, `is_game_over`
- `copy()` barato o suficiente para busca (preferir make/unmake)

Não usar `src/board.py` aqui: `calc_moves` do Pygame é lento demais.

### Passos

1. Dependência `python-chess`.
2. Encapsular `chess.Board` em `engine/board.py`.
3. Testes de regressão contra o jogo atual: mate, afogamento, roque, en passant, promoção.

### Pronto quando

- Perft(position inicial, depth 1) = 20.
- Perft(depth 2) = 400.
- Roque, en passant e promoção passam nos testes.
- Nenhuma importação de `pygame` dentro de `engine/`.

---

## Fase 1 — Engine clássica

Objetivo: oponente jogável só com busca e eval artesanal.

### Arquivos que devem existir

```
engine/search.py
engine/evaluate.py
engine/time_manager.py
engine/api.py
tests/test_search.py
```

### Conteúdo por arquivo

**`evaluate.py`**

- Material: P=100, C=320, B=330, T=500, D=900.
- Piece-square tables (meio-jogo; rei no fim de jogo pode vir depois).
- Sinal do ponto de vista de quem joga.

**`search.py`** (nesta ordem)

1. Negamax com profundidade fixa.
2. Poda alpha-beta.
3. Ordenação: capturas (MVV-LVA), killer moves, history heuristic.
4. Quiescência (só capturas nas folhas).
5. Iterative deepening.
6. Tabela de transposição (hash → valor, profundidade, lance).

**`time_manager.py`**

- Teto por lance (ex.: 5–8% do tempo restante, com mínimo/máximo).

**`api.py`**

- `think(fen, depth=None, nodes=None, time_ms=None) -> str` (UCI).

### Passos

1. Negamax + eval material; jogar profundidade 3 em um script de console.
2. Alpha-beta e confirmar que o lance é o mesmo, com menos nós.
3. Quiescência, ordenação, TT, iterative deepening.
4. Gerência de tempo.

### Pronto quando

- Em `mate in 1`, encontra o mate na profundidade 1–2.
- Profundidade 4–6 joga uma partida completa sem travar.
- Nós/segundo medidos (baseline para a Fase 4).
- Dá para limitar força só com `depth` / `nodes` (skill provisório).

---

## Fase 2 — Rede neural (arquitetura)

Objetivo: definir e instanciar o modelo. Ainda sem treino pesado.

### Arquivos que devem existir

```
engine/encode.py
engine/network.py
tests/test_encode.py
```

### Representação (`encode.py`)

Planos `8×8`, dtype float32, ponto de vista de quem joga (tabuleiro virado se for pretas):

| Planos | Conteúdo |
| --- | --- |
| 12 | Peças (6 brancas + 6 pretas) |
| 1 | Lado a jogar |
| 4 | Direitos de roque |
| 1 | En passant |
| opcional | Xeque, regra das 50 jogadas |

Saída: tensor `(N, C, 8, 8)`.

### Rede (`network.py`) — CNN residual pequena

Não usar transformer nem LLM.

- Stem: Conv 3×3, 64–128 canais.
- 6–10 blocos residuais (Conv 3×3 + BatchNorm + ReLU).
- **Value head:** global average pool → MLP → `tanh` (resultado esperado −1..+1).
- **Policy head:** conv → mapa de lances (origem/destino ou 73 planos estilo AlphaZero).

A policy **não** escolhe o lance sozinha no nível forte; só ordena a lista da busca.

### Passos

1. `encode(fen)` determinístico + testes (espelhamento para pretas).
2. Forward dummy: batch 8, shapes corretos, sem NaN.
3. Salvar/carregar `state_dict` em `models/`.

### Pronto quando

- Encode estável e testado.
- `ValuePolicyNet` instancia, faz forward e grava `models/untrained.pt`.
- Parâmetro count documentado (ordem de 10⁵–10⁶, não dezenas de milhões).

---

## Fase 3 — Treino

Objetivo: pesos nossos, em três estágios.

### Arquivos que devem existir

```
train/dataset.py
train/train.py
train/distill.py
train/selfplay.py
train/eval_match.py
models/value_v1.pt
models/value_v2.pt          # depois da destilação
```

### 3.1 Supervisionado (primeiro treino)

- Fonte: PGN Lichess (filtrar rating alto, ex. 1600+).
- Policy: lance jogado na partida.
- Value: resultado (+1 / 0 / −1) do lado que joga.
- Loss: MSE(value) + cross-entropy(policy).
- Volume útil: 5–20M posições para o primeiro salto; 50M+ se houver disco/tempo.

### 3.2 Destilação com a própria busca

- A engine da Fase 1 (ou a rede já plugada) analisa posições.
- Novo alvo de value: avaliação da busca (ex. depth 6) passada por tanh.
- Retreino → `value_v2.pt`.

### 3.3 Self-play (opcional, mais autoral)

- `selfplay.py`: N partidas engine vs engine.
- Treinar nos jogos gerados.
- Loop: jogar → treinar → trocar pesos → medir vs versão anterior.

### Passos

1. Parser PGN → shards (posição, lance, resultado).
2. `train.py` com validação, checkpoint e log de loss.
3. Destilação num subconjunto.
4. `eval_match.py`: v2 vs v1, 100 partidas, reportar score.

### Pronto quando

- Loss de validação cai de forma estável.
- `models/value_v1.pt` reproduzível (seed + config gravados).
- v2 ganha da v1 em match direto (ou empata com eval claramente melhor em posições-teste).

Não commitar dumps PGN nem `.pt` enormes. Config + script de treino sim.

---

## Fase 4 — Rede dentro da busca

Objetivo: a eval da rede substitui material+PST nas folhas.

### Arquivos que mudam

```
engine/evaluate.py          # passa a chamar a rede (com fallback artesanal)
engine/search.py            # policy para ordenação de lances
engine/api.py               # carrega models/value_v2.pt
```

### Passos

1. Inferência em batch pequeno ou posição a posição; medir ms/posição.
2. Folhas da árvore usam `value` da rede (escala combinável com mate scores).
3. Ordenação: policy primeiro, depois capturas.
4. Comparar nós/s e qualidade vs Fase 1 na mesma profundidade.

### Pronto quando

- Partida completa usando só a eval da rede.
- Em posições táticas de mate curto, a busca ainda encontra o mate.
- Match: Fase 4 vs Fase 1, mesma profundidade — Fase 4 deve ser não-inferior.

---

## Fase 5 — Dificuldades

Objetivo: um cérebro, vários oponentes.

### Arquivos que devem existir

```
engine/skill.py
```

### Níveis

| Nível | Profundidade / nós | Ruído na eval | Sorteio entre lances |
| --- | --- | --- | --- |
| Iniciante | 1–2 | alto | 30–40% não joga o melhor |
| Fácil | 2–3 | médio | 20% |
| Médio | 4 | baixo | 10% |
| Difícil | 6 + rede | quase zero | 0–5% |
| Mestre | tempo 1–3 s, nós altos | zero | sempre o melhor |

Três alavancas em `skill.py`: teto de nós/profundidade, ruído gaussiano na eval, multi-PV + sorteio ponderado.

Opcional depois: policy extra treinada em PGN 800–1200 só para Iniciante/Fácil (erros “humanos”). Fora do caminho crítico.

### Pronto quando

- `think(..., skill="facil")` e `think(..., skill="mestre")` devolvem lances distintos na mesma posição, de forma estável.
- Match interno: Mestre vence Iniciante na maioria das partidas (~80%+).

---

## Fase 6 — Integração no Pygame

Objetivo: o usuário joga contra a engine no app.

### Arquivos que mudam

```
src/settings.py             # opponent, ai_level
src/menu.py                 # vs humano / vs IA + slider
src/main.py                 # turno da IA sem travar o frame loop
src/game.py                 # aplica lance UCI no Board da UI
```

### Passos

1. `GameSettings`: `opponent = "human" | "ai"`, `ai_level = 0..4`.
2. Menu: opção de oponente e dificuldade (além de cor, tema e relógio).
3. Quando `next_player` for a IA: `think` em thread; o relógio da IA corre.
4. Converter UCI → `Move` do `src/` (atenção a promoção e tabuleiro virado).
5. Se o usuário joga de pretas, a IA é brancas.

### Pronto quando

- Partida humana vs IA nos 5 níveis, com tabuleiro virado e relógio.
- UI a 60 FPS enquanto a IA pensa (indicador “pensando…” se precisar).
- Menu → partida → Menu sem vazar thread/estado.

---

## Ordem de implementação (não pular)

```
0 núcleo  →  1 busca clássica  →  2 arquitetura da rede
    →  3 treino  →  4 rede na busca  →  5 skill  →  6 UI
```

Não começar pelo treino. Não começar por AlphaZero/MCTS completo. Self-play só depois de existir busca + encode + um primeiro `value_v1.pt`.

---

## Métricas em todas as fases

| Métrica | Quando |
| --- | --- |
| Perft | Fase 0, sempre que mexer em regras |
| Mate em 1 / 2 | Fase 1 em diante |
| Nós por segundo | Fase 1 vs Fase 4 |
| Loss de treino/validação | Fase 3 |
| Match vN vs vN−1 (100 jogos) | Fase 3–5 |
| Match skill alto vs baixo | Fase 5 |

---

## Fora de escopo (até a Fase 6 terminar)

- Baixar pesos do LC0 ou binário Stockfish como jogador.
- Transformer / GPT escolhendo lances.
- Tablebases Syzygy (podem entrar depois; não são “nosso modelo”).
- Uma rede distinta por nível de dificuldade.
- Reescrever a busca em C++ (só se o Python saturar depois da Fase 4).
