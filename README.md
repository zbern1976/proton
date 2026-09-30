# §PROTON — formato compacto vs prosa na comunicação entre modelos

<img src="docs/logo.svg" width="540" alt="§PROTON — formato compacto entre modelos">

Benchmark mínimo que mede, com números reais de API, se um "formato compacto entre modelos" — o §PROTO v1, batizado §PROTON neste lançamento — economiza tokens e mantém qualidade quando dois modelos de IA debatem por escrito, comparado com texto corrido normal.

## Resultado principal (DeepSeek, n=40 rodadas: 10 itens × 2 condições × 2 réplicas)

| métrica | prosa | §PROTO | delta |
|---|---|---|---|
| entrada (média) | 328,6 | 356,7 | +8,6% (proto mais caro) |
| saída total (média) | 9.961 | 5.980 | −40,0% |
| — raciocínio interno do modelo | 8.395 | 5.459 | −35,0% |
| — resposta líquida | 1.566 | 522 | −66,7% |
| latência | 52,6 s | 29,9 s | −43,2% |
| caracteres/resposta | 5.599 | 1.502 | −73,2% |

Qualidade (juiz LLM cego): cobertura de rubrica 100% nas duas versões; comparador cego A/B: **§PROTO 9 × 8 prosa** (17 pares válidos) — empate técnico com vantagem mínima pro formato compacto.

Leitura: como FORMATO DE RESPOSTA o §PROTO entrega a mesma qualidade com ~1/3 do tamanho e quase metade da latência. Como FORMATO DE ENTRADA não economiza (símbolos custam tokens no tokenizador). O ganho vem do contrato "sem prosa + item a item", não dos símbolos em si.

## O que é o §PROTO v1

Formato compacto inter-modelos. Regra: "Responda SÓ neste formato. Sem prosa. Densidade máxima, zero perda de informação."

✓ concordo · ✗ discordo (+correção) · ? pergunta aberta · → então/implica · ⊕ adicionar · ⊖ cortar · ≈ aproximado · # quantidade · @ fonte/endpoint · ! risco · ~ decisão final.

Spec completa em [docs/PROTO_v1.md](docs/PROTO_v1.md).

## Como reproduzir

1. Clone e instale nada — só Python 3 stdlib.
2. Exporte uma chave: `DEEPSEEK_API_KEY` (ou `ANTHROPIC_API_KEY`).
3. Rode o experimento: `python runner/run_experiment.py --provider deepseek --model deepseek-flash`
4. Avaliação cega: `python judge/judge.py --provider deepseek`
5. Agregado: `python judge/aggregate.py`

## Estrutura

- `fixtures/itens.json` — 10 itens de debate, cada um com a MESMA informação em prosa e em §PROTO + rubrica de avaliação.
- `runner/` — executa o experimento contra a API.
- `judge/` — juiz cego (rubrica binária + comparação A/B com ordem aleatória).
- `results/summary.json` — resultados agregados publicados aqui.
- `docs/` — spec do formato + relatório detalhado.

## Estado

- DeepSeek (deepseek-flash): completo (n=40). Claude: em andamento — os números entram aqui quando a rodada dele fechar.
- Nota metodológica: o modelo usado no braço principal tem raciocínio interno cobrado (~85% dos tokens de saída são "thinking"); a coluna "resposta líquida" separa isso.

## Licença

MIT. Autoria: Bernardo ([@zbern1976](https://github.com/zbern1976)) — desenvolvido com o DeepSeek e o Claude (Anthropic). O §PROTO v1 foi proposto originalmente pelo Claude em sessões de trabalho com o autor (set/2026).
