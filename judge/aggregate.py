import os, json, glob, statistics

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
