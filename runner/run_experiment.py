#!/usr/bin/env python3
"""Roda o experimento PROTO-vs-prosa contra uma API.

Uso:
  export DEEPSEEK_API_KEY=...   # ou ANTHROPIC_API_KEY=...
  python runner/run_experiment.py --provider deepseek --model deepseek-flash [--reps 2]

Salva cada rodada em results/out/<item>_<cond>_r<rep>.json com usage, resposta e latencia.
"""
import os, sys, json, time, argparse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

HOME=os.path.expanduser('~')
BASE=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SUF_PROSA=("\n\n---\nVoce e o colega critico deste debate. Responda a mensagem acima: sua posicao sobre cada ponto, "
           "correcoes concretas e riscos que o autor nao viu. Escreva em portugues, em texto corrido normal.")
SUF_PROTO="\n\n---\nYou are the critic colleague. Reply ONLY in this \u00a7PROTO format (no prose)."

def make_chat(provider, model, key):
    if provider=='deepseek':
        base='https://api.deepseek.com'
        def chat(prompt, temp, max_tokens):
            body={'model':model,'messages':[{'role':'user','content':prompt}],
                  'temperature':temp,'max_tokens':max_tokens,'stream':False}
            req=urllib.request.Request(base+'/chat/completions', data=json.dumps(body).encode(),
                headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'}, method='POST')
            with urllib.request.urlopen(req, timeout=600) as r:
                return json.loads(r.read().decode())
        def unpack(d):
            ch=d['choices'][0]
            return ch['message']['content'], ch.get('finish_reason'), d.get('usage',{}), d.get('model')
        return chat, unpack
    else:  # anthropic
        base='https://api.anthropic.com/v1/messages'
        def chat(prompt, temp, max_tokens):
            body={'model':model,'max_tokens':max_tokens,'temperature':temp,
                  'messages':[{'role':'user','content':prompt}]}
            req=urllib.request.Request(base, data=json.dumps(body).encode(),
                headers={'x-api-key':key,'anthropic-version':'2023-06-01','Content-Type':'application/json'}, method='POST')
            with urllib.request.urlopen(req, timeout=600) as r:
                return json.loads(r.read().decode())
        def unpack(d):
            txt=''.join(b.get('text','') for b in d.get('content',[]) if b.get('type')=='text')
            return txt, d.get('stop_reason'), d.get('usage',{}), d.get('model')
        return chat, unpack

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--provider', choices=['deepseek','anthropic'], default='deepseek')
    ap.add_argument('--model', default='deepseek-flash')
    ap.add_argument('--reps', type=int, default=2)
    ap.add_argument('--max-tokens', type=int, default=16000)
    ap.add_argument('--temperature', type=float, default=0.3)
    args=ap.parse_args()
    key=os.environ.get('DEEPSEEK_API_KEY' if args.provider=='deepseek' else 'ANTHROPIC_API_KEY')
    if not key:
        sys.exit('Falta a chave: export DEEPSEEK_API_KEY (ou ANTHROPIC_API_KEY)')
    chat, unpack=make_chat(args.provider, args.model, key)
    items=json.load(open(f'{BASE}/fixtures/itens.json',encoding='utf-8'))['itens']
    os.makedirs(f'{BASE}/results/out', exist_ok=True)

    def one(item, cond, rep):
        prompt=item[cond]+(SUF_PROSA if cond=='prosa' else SUF_PROTO)
        t0=time.time()
        for attempt in range(3):
            try:
                d=chat(prompt, args.temperature, args.max_tokens)
                resp, fin, usage, used_model=unpack(d)
                rec={'item':item['id'],'cond':cond,'rep':rep,'model':args.model,
                     'model_reported':used_model,'resp':resp,'finish':fin,
                     'usage':usage,'latency_ms':int((time.time()-t0)*1000)}
                json.dump(rec, open(f"{BASE}/results/out/{item['id']}_{cond}_r{rep}.json",'w',encoding='utf-8'),
                          ensure_ascii=False, indent=1)
                return rec
            except Exception as e:
                print('erro', item['id'], cond, rep, str(e)[:120])
                time.sleep(3*(attempt+1))
        return {'item':item['id'],'cond':cond,'rep':rep,'error':'falhou apos 3 tentativas'}

    jobs=[(it,c,r) for it in items for c in ('prosa','proto') for r in range(1,args.reps+1)]
    print(f'{len(jobs)} rodadas | {args.provider}/{args.model} | reps={args.reps}')
    with ThreadPoolExecutor(max_workers=5) as ex:
        for f in as_completed([ex.submit(one,*j) for j in jobs]):
            r=f.result()
            u=r.get('usage') or {}
            print(f"  {r['item']} {r['cond']} r{r['rep']}: in={u.get('prompt_tokens') or u.get('input_tokens')} "
                  f"out={u.get('completion_tokens') or u.get('output_tokens')} fin={r.get('finish')}")
    print('OK — resultados em results/out/')

if __name__=='__main__':
    main()
