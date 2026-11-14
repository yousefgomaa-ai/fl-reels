import urllib.request,urllib.parse,re,html,time,email.utils
SRC=re.compile(r"^(espn|espn fc|espn uk|bbc|bbc sport|bbc news|reuters|associated press|ap news|afp|sky sports|sky news|the athletic|the guardian|the independent|the telegraph|the times|marca|as|as english|mundo deportivo|sport|l'equipe|l'équipe|kicker|la gazzetta dello sport|football italia|record|a bola|o jogo|olé|goal|goal\.com|cbs sports|fox sports|nbc sports|yahoo sports|uefa\.com|fifa|premier league|the standard|evening standard|football\.london|manchester evening news|liverpool echo|talksport|si|sports illustrated|cnn|al jazeera english|bein sports|onefootball|daily mail|mail online)$",re.I)
for n in ["Pep Guardiola","Mikel Arteta","Carlo Ancelotti","Thomas Tuchel","Cristiano Ronaldo","Mohamed Salah"]:
  u="https://news.google.com/rss/search?"+urllib.parse.urlencode({"q":f'"{n}" when:1d',"hl":"en-GB","gl":"GB","ceid":"GB:en"})
  x=urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=15).read().decode()
  print("==",n)
  for it in re.findall(r"<item>(.*?)</item>",x,re.S)[:15]:
    t=html.unescape(re.search(r"<title>(.*?)</title>",it,re.S).group(1)); s=re.search(r"<source[^>]*>(.*?)</source>",it,re.S); s=html.unescape(s.group(1)) if s else ""
    d=email.utils.parsedate_to_datetime(re.search(r"<pubDate>(.*?)</pubDate>",it).group(1)).timestamp(); age=(time.time()-d)/3600
    print(f" {'OK' if SRC.match(s) else '--'} {age:4.1f}h | {s} :: {t[:130]}")
