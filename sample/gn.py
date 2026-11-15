import urllib.request,re,html
F=["https://feeds.bbci.co.uk/sport/football/rss.xml","https://www.skysports.com/rss/12040","https://www.espn.com/espn/rss/soccer/news","https://www.theguardian.com/football/rss","https://www.independent.co.uk/sport/football/rss","https://www.football.london/?service=rss","https://talksport.com/football/feed/","https://www.goal.com/feeds/en/news","https://www.standard.co.uk/sport/football/rss","https://www.manchestereveningnews.co.uk/sport/football/?service=rss","https://www.liverpoolecho.co.uk/sport/football/?service=rss","https://www.mirror.co.uk/sport/football/?service=rss"]
for u in F:
  try:
    x=urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0 (compatible; FootballLegendsBot/1.0; +https://football-legend.com/about)"}),timeout=15).read().decode("utf-8","ignore")
    its=re.findall(r"<item[\s>](.*?)</item>",x,re.S); print("==",u,len(its))
    for it in its[:6]:
      t=re.search(r"<title>(.*?)</title>",it,re.S); d=re.search(r"<description>(.*?)</description>",it,re.S); l=re.search(r"<link>(.*?)</link>",it,re.S); p=re.search(r"<pubDate>(.*?)</pubDate>",it)
      f=lambda m: html.unescape(re.sub(r"<!\[CDATA\[|\]\]>","",m.group(1))).strip() if m else ""
      print("  ",f(p)[:25],"|",f(t)[:110],"|",re.sub("<[^>]+>","",f(d))[:110],"|",f(l)[:90])
  except Exception as e: print("==",u,"ERR",e)
