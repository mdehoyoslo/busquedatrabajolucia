#!/usr/bin/env python3
"""Daily import from Adzuna Spain into Supabase (stdlib only).
Requires ADZUNA_APP_ID, ADZUNA_APP_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY.
Important: the driving-time constraint is NOT confirmed by the API.
"""
import datetime as dt
import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API='https://api.adzuna.com/v1/api/jobs/es/search/1'
# 7 hubs / 4 targeted queries = 28 calls/day (adjust for your API plan).
CITIES=['Madrid','Guadalajara','Toledo','Segovia','Ávila','Valladolid','Cuenca']
QUERIES=['tecnico calidad alimentaria','seguridad alimentaria','auditor alimentaria','APPCC']

MAX_RESULTS=25
# Approximate geographic shortlist. Never claim that a city is within an exact driving-time bound.
REGIONS=('madrid','toledo','guadalajara','segovia','avila','ávila','valladolid','cuenca')
RELEVANCE=('aliment','calidad','appcc','auditor','seguridad alimentaria','trazabilidad','higien','laboratorio','etiquetado','microbiolog')


def http_json(url, method='GET', data=None, headers=None):
    payload=None if data is None else json.dumps(data,ensure_ascii=False).encode('utf-8')
    req=urllib.request.Request(url,data=payload,headers={'Accept':'application/json',**(headers or {})},method=method)
    with urllib.request.urlopen(req,timeout=25) as response:
        raw=response.read()
        return json.loads(raw) if raw else None


def clean(s):
    return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',str(s or '')))).strip()


def normalized(s):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD',str(s).lower()) if unicodedata.category(c)!='Mn')


def relevant(title,desc):
    t=normalized(title);d=normalized(desc)
    if any(x in t for x in ('calidad','aliment','appcc','auditor','laboratorio','higien','etiquet','microbiolog')):
        return True
    return ('tecnico' in t or 'tecnica' in t) and sum(k in d for k in RELEVANCE)>=2


def item_from_ad(ad):
    title=clean(ad.get('title'));desc=clean(ad.get('description'))
    if not relevant(title,desc):return None
    city=clean((ad.get('location') or {}).get('display_name',''))
    if not city or not any(loc in normalized(city) for loc in map(normalized,REGIONS)):
        return None
    url=str(ad.get('redirect_url',''))
    if not url.startswith('https://'):return None
    provider_id=str(ad.get('id') or hashlib.sha256(url.encode()).hexdigest()[:24])
    lo,hi=ad.get('salary_min'),ad.get('salary_max')
    salary=(f'{lo:,.0f}–{hi:,.0f} € bruto/año' if isinstance(lo,(int,float)) and isinstance(hi,(int,float)) and 0<lo<=hi else None)
    return {'source':'adzuna','source_id':provider_id,'title':title[:220],
            'company':clean((ad.get('company') or {}).get('display_name','No indicado'))[:180],
            'city':city[:180],'url':url,'description':desc[:6000], 'salary':salary,
            'published_at':ad.get('created'),
            'last_seen_at':dt.datetime.now(dt.timezone.utc).isoformat()}


def main():
    required=['ADZUNA_APP_ID','ADZUNA_APP_KEY','SUPABASE_URL','SUPABASE_SERVICE_ROLE_KEY']
    missing=[x for x in required if not os.getenv(x)]
    if missing:raise RuntimeError('Missing secrets: '+', '.join(missing))
    sb=os.environ['SUPABASE_URL'].rstrip('/')
    if not sb.startswith('https://'):raise ValueError('SUPABASE_URL must be HTTPS')
    ads={};successful=0;failures=[]
    for city in CITIES:
      for term in QUERIES:
        params={'app_id':os.environ['ADZUNA_APP_ID'],'app_key':os.environ['ADZUNA_APP_KEY'],
                'results_per_page':MAX_RESULTS,'what':term,'where':city,'sort_by':'date','max_days_old':'14',
                'content-type':'application/json'}
        url=API+'?'+urllib.parse.urlencode(params)
        try:
          results=http_json(url)
          successful+=1
          for ad in (results.get('results') or []):
            record=item_from_ad(ad)
            if record:ads[record['source_id']]=record
        except Exception as ex:
          # Never log URL: it contains the Adzuna key!
          failures.append(f'{city}/{term}: {type(ex).__name__} {getattr(ex,"code","")}')
        time.sleep(0.15)
    if not successful:raise RuntimeError('All Adzuna searches failed: '+ '; '.join(failures[:6]))
    print(f'Successful searches: {successful}/{len(CITIES)*len(QUERIES)}; unique matching: {len(ads)}')
    if failures:print('Some searches failed: '+'; '.join(failures[:5]),file=sys.stderr)
    # PUT only the automatically refreshed public fields; do NOT overwrite status/favorite/notes.
    # PostgREST upsert with on_conflict merges provided columns only.
    headers={'apikey':os.environ['SUPABASE_SERVICE_ROLE_KEY'],
             'Authorization':'Bearer '+os.environ['SUPABASE_SERVICE_ROLE_KEY'],
             'Content-Type':'application/json','Prefer':'resolution=merge-duplicates,return=minimal'}
    items=list(ads.values())
    for i in range(0,len(items),100):
        http_json(sb+'/rest/v1/jobs?on_conflict=source,source_id',method='POST',data=items[i:i+100],headers=headers)
    print(f'Upserted: {len(items)}. Existing application statuses untouched.')

if __name__=='__main__':
    try:main()
    except Exception as e:print('ERROR:',str(e),file=sys.stderr);sys.exit(1)
