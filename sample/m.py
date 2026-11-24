import json
for d in ['20261124','20261125']:
  try: j=json.load(open('m'+d+'.json'))
  except Exception as e: print(d,'ERR',e); continue
  evs=j.get('events') or j.get('matches') or j.get('response') or (j if isinstance(j,list) else [])
  if isinstance(j,dict) and not evs: print(d,list(j.keys())[:10]); continue
  print(d,'events',len(evs))
  for m in evs:
    s=json.dumps(m)
    if '575398' in s or 'Galatasaray' in s:
      print(d, json.dumps({k:m.get(k) for k in ('id','leagueSlug','goals','score','fixture','teams','liveSource','penalties')},ensure_ascii=False)[:1500])
