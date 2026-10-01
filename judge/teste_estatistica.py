# -*- coding: utf-8 -*-
"""
Testes de sanidade para judge/estatistica.py.

Nao precisa de pytest nem de nada instalado:

    python judge/teste_estatistica.py

A ideia e simples: antes de confiar num p-valor calculado sobre os dados reais,
o teste tem que acertar os casos em que a resposta certa ja e conhecida.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import estatistica as e

falhas = []


def checa(descricao, condicao, obtido=None):
    if condicao:
        print("  ok   %s" % descricao)
    else:
        print("  FALHOU  %s  (obtido: %r)" % (descricao, obtido))
        falhas.append(descricao)


print("permutacao pareada")

obvio = [(100, 50), (200, 90), (150, 70), (300, 140), (120, 55),
         (180, 85), (90, 44), (250, 120), (160, 75), (210, 100)]
r = e.permutacao_pareada(obvio)
checa("diferenca grande e consistente da p < 0.05", r["p_valor"] < 0.05, r["p_valor"])
checa("com 10 itens o teste roda exato", "exato" in r["modo"], r["modo"])
checa("a diferenca media sai negativa quando o proto gasta menos",
      r["diferenca_media"] < 0, r["diferenca_media"])

r = e.permutacao_pareada([(100, 100)] * 10)
checa("sem diferenca nenhuma da p = 1", r["p_valor"] == 1.0, r["p_valor"])

r = e.permutacao_pareada([(100, 101), (100, 99), (100, 102), (100, 98), (100, 100),
                          (100, 103), (100, 97), (100, 101), (100, 99), (100, 100)])
checa("ruido simetrico nao vira significancia", not r["significativo_5pct"], r["p_valor"])

checa("lista vazia devolve None", e.permutacao_pareada([]) is None)

print("binomial bicaudal")
checa("9 de 17 e o empate mais perfeito possivel: p = 1",
      e.binomial_bicaudal(9, 17) == 1.0, e.binomial_bicaudal(9, 17))
checa("vitoria unanime da p praticamente zero",
      e.binomial_bicaudal(17, 17) < 0.001, e.binomial_bicaudal(17, 17))
checa("14 de 17 ja passa do corte de 5%",
      e.binomial_bicaudal(14, 17) < 0.05, e.binomial_bicaudal(14, 17))
checa("metade exata de uma amostra par da p = 1",
      e.binomial_bicaudal(10, 20) == 1.0, e.binomial_bicaudal(10, 20))

print("intervalo de Wilson")
w = e.wilson(9, 17)
checa("o IC do nosso placar cobre os 50%",
      w["ic95_inferior"] < 50 < w["ic95_superior"], w)
checa("o IC nunca passa de 100%", e.wilson(17, 17)["ic95_superior"] <= 100.0)
checa("o IC nunca fica negativo", e.wilson(0, 17)["ic95_inferior"] >= 0.0)

print("tamanho de amostra")
n60 = e.pares_necessarios(0.60)
n55 = e.pares_necessarios(0.55)
checa("detectar uma vantagem menor exige mais pares", n55 > n60, (n60, n55))
checa("nenhum dos dois cabe nos 17 pares que temos", n60 > 17 and n55 > 17, (n60, n55))

print("veredito do juiz cego, com os numeros reais do benchmark")
v = e.veredito_cego(9, 8)
checa("o veredito e empate", v["conclusao"].startswith("empate"), v["conclusao"])
checa("o placar sai formatado certo", v["placar"] == "9 x 8", v["placar"])
checa("conta 17 pares", v["pares"] == 17, v["pares"])

print("resumo e bootstrap")
amostra = [9961, 10200, 9800, 10050, 9700]
s = e.resumo(amostra)
checa("o n bate com a amostra", s["n"] == 5, s["n"])
checa("o desvio e positivo", s["desvio"] > 0, s["desvio"])
ic = e.ic_bootstrap(amostra)
checa("a media cai dentro do proprio IC",
      ic["ic95_inferior"] <= s["media"] <= ic["ic95_superior"], (ic, s["media"]))
checa("valores nulos sao ignorados em vez de quebrar",
      e.resumo([1, None, 3])["n"] == 2)
checa("amostra de um elemento so nao gera IC", e.ic_bootstrap([42]) is None)

print()
if falhas:
    print("%d teste(s) falharam" % len(falhas))
    sys.exit(1)
print("todos os testes passaram")
