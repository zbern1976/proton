# -*- coding: utf-8 -*-
"""
Incerteza e significancia para os resultados do benchmark.

Tudo com a biblioteca padrao, igual ao resto do repo: nenhuma dependencia nova.

Os testes sao exatos, nao aproximados:
  - permutacao pareada: com 10 itens sao 2**10 = 1024 trocas de sinal possiveis,
    entao da pra enumerar todas em vez de amostrar;
  - binomial: enumera a distribuicao inteira.

O desenho e pareado de proposito. Cada item roda nas duas condicoes, entao a
comparacao certa e item a item, nao media contra media: isso remove a variacao
entre itens, que aqui e grande.
"""
from itertools import product
from math import comb, erf, sqrt
from statistics import mean, median, stdev

Z95 = 1.959964


def resumo(valores):
    """Media, mediana, desvio e erro padrao de uma amostra."""
    xs = [float(v) for v in valores if v is not None]
    if not xs:
        return None
    n = len(xs)
    dp = stdev(xs) if n > 1 else 0.0
    return {
        "n": n,
        "media": round(mean(xs), 1),
        "mediana": round(median(xs), 1),
        "desvio": round(dp, 1),
        "erro_padrao": round(dp / sqrt(n), 1) if n > 1 else 0.0,
        "min": round(min(xs), 1),
        "max": round(max(xs), 1),
    }


def ic_bootstrap(valores, reamostragens=20000, semente=20261001):
    """IC95% da media por bootstrap percentil. Nao assume normalidade."""
    xs = [float(v) for v in valores if v is not None]
    n = len(xs)
    if n < 2:
        return None

    # gerador linear congruente, so pra nao depender de nada externo
    estado = semente
    def proximo_indice():
        nonlocal estado
        estado = (1103515245 * estado + 12345) % (2 ** 31)
        return estado % n

    medias = []
    for _ in range(reamostragens):
        medias.append(sum(xs[proximo_indice()] for _ in range(n)) / n)
    medias.sort()
    lo = medias[int(0.025 * reamostragens)]
    hi = medias[int(0.975 * reamostragens) - 1]
    return {"ic95_inferior": round(lo, 1), "ic95_superior": round(hi, 1)}


def permutacao_pareada(pares, exato_ate=20):
    """
    Teste de permutacao pareado sobre a diferenca dentro de cada item.

    `pares` e uma lista de (valor_prosa, valor_proto), um por item.
    H0: trocar as duas condicoes de lugar nao muda nada, ou seja, o sinal da
    diferenca de cada item e tao provavel positivo quanto negativo.

    Com poucos itens enumera todas as 2**n trocas de sinal e devolve o p-valor
    exato. Acima disso, amostra.
    """
    difs = [float(b) - float(a) for a, b in pares if a is not None and b is not None]
    n = len(difs)
    if n == 0:
        return None

    observado = abs(mean(difs))

    if n <= exato_ate:
        extremos = 0
        total = 0
        for sinais in product((1, -1), repeat=n):
            total += 1
            if abs(sum(s * d for s, d in zip(sinais, difs)) / n) >= observado - 1e-12:
                extremos += 1
        p = extremos / total
        modo = "exato (%d permutacoes)" % total
    else:
        estado = 20261001
        extremos = total = 0
        for _ in range(50000):
            soma = 0.0
            for d in difs:
                estado = (1103515245 * estado + 12345) % (2 ** 31)
                soma += d if estado % 2 else -d
            total += 1
            if abs(soma / n) >= observado - 1e-12:
                extremos += 1
        p = (extremos + 1) / (total + 1)
        modo = "amostrado (50k permutacoes)"

    return {
        "n_pares": n,
        "diferenca_media": round(mean(difs), 1),
        "p_valor": round(p, 4),
        "modo": modo,
        "significativo_5pct": p < 0.05,
    }


def binomial_bicaudal(vitorias, total):
    """P de ver um placar tao desequilibrado quanto este, se nao houvesse diferenca."""
    if total == 0:
        return None
    pmf = [comb(total, i) * 0.5 ** total for i in range(total + 1)]
    alvo = pmf[vitorias]
    p = sum(x for x in pmf if x <= alvo + 1e-12)
    return round(min(1.0, p), 4)


def wilson(vitorias, total):
    """IC95% de uma proporcao. Wilson aguenta n pequeno melhor que o normal."""
    if total == 0:
        return None
    phat = vitorias / total
    den = 1 + Z95 ** 2 / total
    centro = (phat + Z95 ** 2 / (2 * total)) / den
    meia = Z95 * sqrt(phat * (1 - phat) / total + Z95 ** 2 / (4 * total ** 2)) / den
    return {
        "taxa": round(phat * 100, 1),
        "ic95_inferior": round(max(0.0, centro - meia) * 100, 1),
        "ic95_superior": round(min(1.0, centro + meia) * 100, 1),
    }


def pares_necessarios(taxa_real, poder_alvo=0.80):
    """Quantos pares cegos seriam precisos pra enxergar uma vantagem desse tamanho."""
    for n in range(10, 20000):
        se0 = sqrt(0.25 / n)
        se1 = sqrt(taxa_real * (1 - taxa_real) / n)
        critico = Z95 * se0
        poder = 0.5 * (1 + erf(((taxa_real - 0.5) - critico) / (se1 * sqrt(2))))
        if poder >= poder_alvo:
            return n
    return None


def veredito_cego(vitorias_proto, vitorias_prosa):
    """Fecha o placar do juiz cego com p-valor, IC e o tamanho de amostra que faltaria."""
    total = vitorias_proto + vitorias_prosa
    if total == 0:
        return None
    w = wilson(vitorias_proto, total)
    p = binomial_bicaudal(vitorias_proto, total)
    return {
        "placar": "%d x %d" % (vitorias_proto, vitorias_prosa),
        "pares": total,
        "taxa_vitoria_proto_pct": w["taxa"],
        "ic95_pct": [w["ic95_inferior"], w["ic95_superior"]],
        "p_valor": p,
        "conclusao": (
            "empate: o intervalo de confianca cobre os dois lados, "
            "entao estes dados nao sustentam vantagem de qualidade pra nenhum formato"
            if w["ic95_inferior"] < 50 < w["ic95_superior"]
            else "diferenca detectada"
        ),
        "pares_para_detectar_60_40": pares_necessarios(0.60),
        "pares_para_detectar_55_45": pares_necessarios(0.55),
    }
