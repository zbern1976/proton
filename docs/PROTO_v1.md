# §PROTON (ex-§PROTO v1) — formato compacto entre modelos

> "Responda SÓ neste formato. Sem prosa. Densidade máxima, zero perda de informação."

> Nome: o formato nasceu como "§PROTO v1" e foi batizado **§PROTON** para o lançamento público — o próton é a partícula que troca sinais com as outras; é exatamente o que este formato faz entre modelos.

## O que é

Um formato de RESPOSTA para debates entre modelos de IA (ou entre modelos e orquestradores): cada linha é uma posição — item, veredito e correção — em vez de parágrafos. A intenção é cortar a "embalagem" do texto ("ótima pergunta", "concordo em grande parte, porém…", resumos repetidos) sem perder conteúdo: número, fonte, risco e decisão continuam obrigatórios.

Não é uma linguagem nova nem uma cifra: usa símbolos e abreviações que qualquer modelo já conhece, e a legenda pode ser traduzida ("legenda pra humano ler").

## Legenda (símbolos fixos)

| símbolo | significado |
|---|---|
| ✓ | concordo |
| ✗ | discordo (com a correção junto) |
| ? | pergunta aberta |
| → | então / implica |
| ⊕ | adicionar |
| ⊖ | cortar |
| ≈ | aproximado |
| # | quantidade |
| @ | fonte / endpoint |
| ! | risco |
| ~ | decisão final |

Abreviações de domínio ("keys") mudam por projeto: cada debate declara as suas no cabeçalho (ex.: `stn=estação`, `fc=previsão`, `L=aluno`, `ex=exercício`).

## Estrutura de uma mensagem

```
§PROTO v1 (compact inter-model). Reply ONLY in this format. No prose. Max density, zero info loss.
LEGEND: <símbolos usados nesta conversa>
CTX: <1 linha de contexto — onde estamos, o que já foi acordado>
C.prop:                       # ou C.crit (crítica)
 P1 <proposta/item 1>
 P2 <proposta/item 2>
 ?1 <pergunta aberta 1>
OUT: per item ✓/✗+fix; ⊕/⊖; answers ?k; final ~ list.
```

Convenções: `C.prop`/`C.crit` marcam o autor do bloco; `P1..Pn` são os itens; `OUT` declara o formato esperado da resposta. O que não for coberto pelo formato vira `⊕` ou `?` — nunca se perde.

## Exemplo

```
CTX: MVP do coletor (1 cidade, sqlite, paper-only). Acordo r1-r2 firmado.
C.crit:
 P1 ✗ fix: previsão de grade não equivale à máxima horária na estação — converter dia/fuso/arredondamento.
 P2 ✓ com condição: persistir regras de liquidação por mercado (fonte, fallback, unidade, precisão).
 ?1 parse de regras: regex ou LLM?
 ⊕: detector de faixa impossível (não precisa de modelo meteorológico).
 ~: manter P1 corrigido, P2 condicionado; ?1 → regex primeiro, LLM só no fallback.
```

## Por que funciona (e por que não em todo lugar)

- Funciona como FORMATO DE RESPOSTA: medido em −40% tokens totais / −67% na resposta líquida / −43% latência, com qualidade igual (ver README).
- Não funciona como formato de ENTRADA (+8,6% tokens): símbolos raros e "cola" sem espaços viram múltiplos tokens no tokenizador BPE; escrever assim não comprime o que o modelo lê.
- O ganho vem do contrato de brevidade e da estrutura item-a-item — não dos símbolos. Símbolos exóticos (∴, ⟹) pioram: custam mais tokens e aumentam o risco de leitura errada.

## Histórico

- Proposto pelo Claude (Anthropic) em sessão de trabalho com o autor, rodada r3 do debate de um bot de previsão (26/09/2026), com o nome original "§PROTO v1".
- Adotado em produção num segundo debate (app de ensino de C, rodadas r1–r8), com a legenda traduzida para humanos.
- Validado quantitativamente em 30/09/2026 pelo benchmark deste repositório — e lançado como §PROTON.
