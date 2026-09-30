import os, json, time, random, urllib.request, re
from concurrent.futures import ThreadPoolExecutor, as_completed

HOME=os.path.expanduser('~'); BASE=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
k=os.environ.get('DEEPSEEK_API_KEY'); u=os.environ.get('DEEPSEEK_BASE_URL')
if not k:
    try:
        for ln in open(HOME+'/AppData/Local/hermes/.env',encoding='utf-8',errors='ignore'):
            if not k and ln.startswith('DEEPSEEK_API_KEY='): k=ln.split('=',1)[1].strip()
            if not u and ln.startswith('DEEPSEEK_BASE_URL='): u=ln.split('=',1)[1].strip()
    except Exception: pass
BASE_URL=(u or 'https://api.deepseek.com').rstrip('/')

def chat(prompt, max_tokens=4000, timeout=300):
    body={'model':'deepseek-flash','messages':[{'role':'user','content':prompt}],'temperature':0.0,'max_tokens':max_tokens,'stream':False}
    req=urllib.request.Request(BASE_URL+'/chat/completions', data=json.dumps(body).encode(), headers={'Authorization':'Bearer '+k,'Content-Type':'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

def seg(resp):
    resp=resp or ''
    if len(resp)<=12000: return resp
    return resp[:8000] + '\n...[TRECHO OMITIDO]...\n' + resp[-3500:]

items={}
for it in json.load(open(f'{BASE}/fixtures/itens.json',encoding='utf-8'))['itens']:
    items[it['id']]=it

try:
    prev=json.load(open(f'{BASE}/results/judge_checks.json',encoding='utf-8'))
except FileNotFoundError:
    prev=[]
have={(x['item'],x['cond'],x['rep']) for x in prev if x.get('checks')}
todo=[(it,c,r) for it in items for c in ('prosa','proto') for r in (1,2) if (it,c,r) not in have]
print('checks ainda faltantes:', len(todo))

def do_check(job):
    item_id,cond,rep=job
    it=items[item_id]
    out=json.load(open(f'{BASE}/results/out/{item_id}_{cond}_r{rep}.json',encoding='utf-8'))
    if not out.get('resp'): return None
    rub=it['rubrica']; n=len(rub)
    rub_txt='\n'.join(f'{i+1}. {r}' for i,r in enumerate(rub))
    prompt=(f"AVALIADOR RIGOROSO. Ha uma mensagem de debate, a resposta de um modelo e uma rubrica com {n} pontos.\n"
            f"Para cada ponto, marque 1 se a resposta de fato aborda o ponto, 0 se nao (vago = 0).\n"
            f"Responda SOMENTE uma linha com {n} numeros (0 ou 1) separados por espaco. Nada alem da linha.\n"
            f"MENSAGEM:\n{it[cond][:6000]}\nRESPOSTA:\n{seg(out['resp'])}\nRUBRICA:\n{rub_txt}\n")
    for attempt in range(5):
        try:
            d=chat(prompt)
            txt=d['choices'][0]['message']['content'].strip()
            nums=re.findall(r'[01]', txt)
            if len(nums)==n:
                return {'item':item_id,'cond':cond,'rep':rep,'checks':[int(x) for x in nums]}
        except Exception as e:
            time.sleep(2)
        time.sleep(1)
    return {'item':item_id,'cond':cond,'rep':rep,'checks':None,'raw_head':txt[:200] if 'txt' in dir() else ''}

new=[]
with ThreadPoolExecutor(max_workers=6) as ex:
    for f in as_completed([ex.submit(do_check,j) for j in todo]):
        r=f.result()
        if r:
            new.append(r); print('check', r['item'], r['cond'], r['rep'], r.get('checks'))
final=[x for x in prev if x.get('checks')]+new
json.dump(final, open(f'{BASE}/results/judge_checks.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
print('checks completos:', sum(1 for x in final if x.get('checks')))

try:
    prev2=json.load(open(f'{BASE}/results/judge_sbs.json',encoding='utf-8'))
except FileNotFoundError:
    prev2=[]
have2={(x['item'],x['rep']) for x in prev2 if x.get('melhor')}
todo2=[(it,r) for it in items for r in (1,2) if (it,r) not in have2]
print('sbs ainda faltantes:', len(todo2))

def do_sbs(job):
    item_id,rep=job
    it=items[item_id]
    try:
        a=json.load(open(f'{BASE}/results/out/{item_id}_prosa_r{rep}.json',encoding='utf-8'))
        b=json.load(open(f'{BASE}/results/out/{item_id}_proto_r{rep}.json',encoding='utf-8'))
    except Exception: return None
    if not a.get('resp') or not b.get('resp'): return None
    rng=random.Random(f'{item_id}-{rep}-v2')
    if rng.random()<0.5: first,second,map_=a,b,{'1':'prosa','2':'proto'}
    else: first,second,map_=b,a,{'1':'proto','2':'prosa'}
    rub_txt='; '.join(it['rubrica'])
    prompt=(f"COMPARADOR CEGO. RESP-1 e RESP-2 respondem a mesma mensagem (uma em texto normal, outra em formato compacto; voce nao sabe qual e qual).\n"
            f"Pontos que uma boa resposta deveria cobrir: {rub_txt}\n"
            f"Qual das duas cobre melhor esses pontos, com menos enrolacao e mais precisao?\n"
            f"Responda SOMENTE com o numero: 1 (RESP-1 melhor), 2 (RESP-2 melhor) ou 0 (empate). Nada mais.\n"
            f"MENSAGEM:\n{it['prosa'][:4000]}\nRESP-1:\n{seg(first['resp'])}\nRESP-2:\n{seg(second['resp'])}\n")
    for attempt in range(5):
        try:
            d=chat(prompt)
            txt=d['choices'][0]['message']['content'].strip()
            m=re.search(r'[012]', txt)
            if m:
                val=m.group(0)
                cond_map={'1':map_['1'],'2':map_['2'],'0':'empate'}
                return {'item':item_id,'rep':rep,'melhor':val,'melhor_cond':cond_map[val],'motivo':'', 'ordem':map_}
        except Exception as e:
            time.sleep(2)
        time.sleep(1)
    return {'item':item_id,'rep':rep,'melhor':None,'raw_head':txt[:200] if 'txt' in dir() else ''}

new2=[]
with ThreadPoolExecutor(max_workers=6) as ex:
    for f in as_completed([ex.submit(do_sbs,j) for j in todo2]):
        r=f.result()
        if r:
            new2.append(r); print('sbs', r['item'], r['rep'], r.get('melhor_cond'))
final2=[x for x in prev2 if x.get('melhor')]+new2
json.dump(final2, open(f'{BASE}/results/judge_sbs.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
print('sbs completos:', sum(1 for x in final2 if x.get('melhor')))
