# ChessAI

Jogo de xadrez local para dois jogadores, feito em Python com Pygame. Inclui regras oficiais (roque, en passant, promoção, xeque-mate e afogamento), relógio de tempo, temas de tabuleiro e histórico de lances.

O projeto foi inspirado no tutorial: [How to Code Chess in Python](https://www.youtube.com/watch?v=OpL0Gcfn4B4).

O plano da engine própria (fases, pastas e critérios de pronto) está em [docs/ENGINE_PLAN.md](docs/ENGINE_PLAN.md).

## Requisitos

- Python 3.10 ou superior
- Pygame, python-chess, numpy, PyTorch, pytest

## Como executar

Na raiz do repositório:

```bash
pip install -r requirements.txt
python src/main.py
```

Execute a partir da raiz do projeto (`ChessAI/`), não de `src/`. Os sprites e sons em `assets/` são carregados com caminhos relativos.

## Engine

Duas IAs, a mesma busca nossa:

- **Própria** — CNN treinada só com Lichess (`models/value_v1.pt`). Tentativa 100% nossa. A rede só ordena lances na raiz; a árvore usa eval clássica.
- **Destilada** — MLP compacta nossa (`models/value_sf.pt`) com **rótulos do Stockfish**. O SF não joga no app; só ensina eval e o melhor lance. A rede entra nas folhas (é barata o bastante).

```powershell
pytest
python -m engine 4
```

### Destilada (deixar rodando à noite)

Usa o JSONL de Elo alto que você já tem. Baixa o Stockfish se precisar, rotula por ~9 h e treina ~1 h:

```powershell
python -m train.sf_teacher --hours 10
```

Quando terminar, existe `models/value_sf.pt`. No jogo: **Oponente → Destilada** → Difícil ou Mestre.

Se a rotulagem parar no meio, o arquivo `data/sf_labels.jsonl` permanece. Depois:

```powershell
python -m train.sf_teacher --train-only
```

Treino só da CNN própria (sem Stockfish):

```powershell
python -m train.train --data data/lichess_high_elo.jsonl --val data/lichess_high_elo_val.jsonl --out models/value_v1.pt
```

No menu: **Própria** ou **Destilada** + dificuldade. A engine pensa numa thread (o jogo não trava).

## Como jogar

1. No menu inicial, clique em **Jogar**.
2. Escolha oponente (**Humano**, **Própria** ou **Destilada**), dificuldade, a cor com que você joga, o tema e o controle de tempo.
3. Clique em **Jogar**.
4. Clique numa peça para selecioná-la e depois na casa de destino para mover. Também é possível arrastar a peça.
5. Use **Menu** na barra lateral para voltar ao menu.

### Temas

Verde, Marrom, Azul e Roxo.

### Controles de tempo

| Opção | Tempo por jogador |
| --- | --- |
| 1 min | Bullet |
| 3 min / 5 min | Blitz |
| 10 min / 15 min | Rapid |
| Sem tempo | sem relógio |

O relógio começa após o primeiro lance. Se o tempo de um jogador chegar a zero, o adversário vence.

## Controles

| Ação | Tecla / mouse |
| --- | --- |
| Mover peça | clicar para selecionar e clicar na casa, ou arrastar |
| Tela cheia | `F11` |
| Reiniciar partida | `R` |
| Voltar ao menu | botão **Menu** |
| Sair | **Sair** no menu ou fechar a janela |

A janela é redimensionável.

## Estrutura

```
ChessAI/
├── assets/
├── engine/          # regras, busca, rede
├── train/           # self-play e treino
├── models/          # checkpoints .pt
├── src/             # jogo (Pygame)
├── tests/
└── README.md
```
