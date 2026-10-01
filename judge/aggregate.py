import os, json, glob, statistics, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import estatistica as est

HOME=os.path.expanduser('~'); BASE=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
SYMS='\u2713\u2717\u2192\u2295\u2296\u2248#@!~?'

rows=[]
for f in sorted(glob.glob(BASE+'/results/out/*.json')):
    o=json.load(open(f,encoding='utf-8'))
    if not o.get('resp'): continue
    r=o['resp']; u=o.get('usage') or {}
    det=u.get('completion_tokens_details') or {}
    reason=det.get('reasoning_tokens', 0) if isinstance(det, dict) else 0
    out_total=u.get('completion_tokens')
    nlines=[l for l in r.split('\n') if l.strip()]
    sym_lines=[l for l in nlines if l.strip() and l.strip()[0] in SYMS]
    rows.append({
        'item':o['item'],'cond':o['cond'],'rep':o['rep'],
        'in':u.get('prompt_tokens'),'out':out_total,
        'reason':reason if isinstance(out_total,int) else None,
        'resp':(out_total-reason) if isinstance(out_total,int) and isinstance(reason,int) else None,
        'lat':o.get('latency_ms'),'chars':len(r),
        'sym_lines':len(sym_lines),'lines':len(nlines),
        'sym_total':sum(r.count(s) for s in SYMS),
        'finish':o.get('finish'),
    })

def stats(key, cond):
    xs=[r[key] for r in rows if r['cond']==cond and r[key] is not None]
    if not xs: return None
    return {'n':len(xs),'mean':round(statistics.mean(xs),1),'median':round(statistics.median(xs),1),'min':min(xs),'max':max(xs)}

out={'per_cond':{}, 'per_item':{}, 'conform':{}}
for cond in ('prosa','proto'):
    out['per_cond'][cond]={k:stats(k,cond) for k in ('in','out','reason','resp','lat','chars','sym_total')}

for item in sorted(set(r['item'] for r in rows)):
    out['per_item'][item]={}
    for cond in ('prosa','proto'):
        xs=[r for r in rows if r['item']==item and r['cond']==cond]
        out['per_item'][item][cond]={k:round(statistics.mean([x[k] for x in xs]),1) for k in ('in','out','lat','chars')}

for cond in ('prosa','proto'):
    rr=[r for r in rows if r['cond']==cond]
    frac=[ (r['sym_lines']/r['lines'] if r['lines'] else 0) for r in rr ]
    out['conform'][cond]={'media_frac_linhas_com_simbolo':round(statistics.mean(frac),3),
                          'media_simbolos_por_resposta':round(statistics.mean([r['sym_total'] for r in rr]),1)}

# ---------------------------------------------------------------- incerteza
# Media sozinha nao diz se a diferenca e real. Como cada item roda nas duas
# condicoes, da pra comparar item a item (pareado) e perguntar: se as duas
# condicoes fossem iguais, com que frequencia veriamos uma diferenca destas?
out['incerteza'] = {}
for cond in ('prosa', 'proto'):
    out['incerteza'][cond] = {}
    for k in ('in', 'out', 'resp', 'lat', 'chars'):
        xs = [r[k] for r in rows if r['cond'] == cond and r[k] is not None]
        if xs:
            out['incerteza'][cond][k] = est.resumo(xs)
            out['incerteza'][cond][k].update(est.ic_bootstrap(xs) or {})

out['teste_pareado'] = {}
for k in ('in', 'out', 'resp', 'lat', 'chars'):
    pares = []
    for item in sorted(set(r['item'] for r in rows)):
        a = [r[k] for r in rows if r['item'] == item and r['cond'] == 'prosa' and r[k] is not None]
        b = [r[k] for r in rows if r['item'] == item and r['cond'] == 'proto' and r[k] is not None]
        if a and b:
            pares.append((statistics.mean(a), statistics.mean(b)))
    r = est.permutacao_pareada(pares)
    if r:
        out['teste_pareado'][k] = r

# placar do juiz cego, se ja tiver rodado
try:
    sbs = json.load(open(BASE+'/results/judge_sbs.json', encoding='utf-8'))
    vit = {'proto': 0, 'prosa': 0, 'empate': 0}
    for x in sbs:
        c = x.get('melhor_cond')
        if c in vit:
            vit[c] += 1
    if vit['proto'] + vit['prosa'] > 0:
        out['juiz_cego'] = est.veredito_cego(vit['proto'], vit['prosa'])
        out['juiz_cego']['empates_descartados'] = vit['empate']
except FileNotFoundError:
    pass

json.dump(out, open(BASE+'/results/aggregated.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)

print('=== AGG DeepSeek (n=40; 2 reps por celula) ===')
for cond in ('prosa','proto'):
    c=out['per_cond'][cond]
    print(f"{cond}: IN {c['in']['mean']} | OUT {c['out']['mean']} (med {c['out']['median']}) | reason {c['reason']['mean']} | resp {c['resp']['mean']} | lat {c['lat']['mean']}ms | chars {c['chars']['mean']}")
print()
d_in = out['per_cond']['proto']['in']['mean']/out['per_cond']['prosa']['in']['mean']
d_out= out['per_cond']['proto']['out']['mean']/out['per_cond']['prosa']['out']['mean']
d_lat= out['per_cond']['proto']['lat']['mean']/out['per_cond']['prosa']['lat']['mean']
print(f'DELTA proto vs prosa: IN {d_in:.3f}x | OUT {d_out:.3f}x | lat {d_lat:.3f}x')
print()
print('=== POR ITEM (in/out) ===')
for item in sorted(out['per_item']):
    p=out['per_item'][item]['prosa']; q=out['per_item'][item]['proto']
    print(f"{item}: prosa in={p['in']} out={p['out']} | proto in={q['in']} out={q['out']}")
print()
print('=== CONFORMIDADE (fracao de linhas que comecam com simbolo) ===')
for cond in ('prosa','proto'):
    print(cond, out['conform'][cond])
print()
print('=== INCERTEZA (media +- desvio, IC95% por bootstrap) ===')
for cond in ('prosa','proto'):
    for k in ('out','resp','lat'):
        s=out['incerteza'][cond].get(k)
        if s:
            print(f"{cond:6s} {k:5s}: {s['media']} +- {s['desvio']} "
                  f"(IC95 {s.get('ic95_inferior')}..{s.get('ic95_superior')}, n={s['n']})")
print()
print('=== TESTE PAREADO item a item (permutacao exata) ===')
print('H0: trocar prosa por proto nao muda nada')
for k, t in out['teste_pareado'].items():
    marca='SIGNIFICATIVO' if t['significativo_5pct'] else 'nao significativo'
    print(f"  {k:5s}: diferenca media {t['diferenca_media']:>9} | p={t['p_valor']:.4f} | {marca} | {t['modo']}")
if 'juiz_cego' in out:
    j=out['juiz_cego']
    print()
    print('=== JUIZ CEGO ===')
    print(f"  placar {j['placar']} em {j['pares']} pares ({j['empates_descartados']} empates descartados)")
    print(f"  taxa de vitoria do proto: {j['taxa_vitoria_proto_pct']}% "
          f"(IC95 {j['ic95_pct'][0]}..{j['ic95_pct'][1]}%)  p={j['p_valor']}")
    print(f"  -> {j['conclusao']}")
    print(f"  pra detectar 60/40 seriam precisos ~{j['pares_para_detectar_60_40']} pares; "
          f"pra 55/45, ~{j['pares_para_detectar_55_45']}")
