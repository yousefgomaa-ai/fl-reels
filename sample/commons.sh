#!/bin/bash
# One-off: Commons files of a player, with a small thumb of each to check by eye.
set -e; q="$1"; out=sample/look; mkdir -p $out
UA="FootballLegendsBot/1.0 (https://football-legend.com/contact/)"
curl -sS -A "$UA" "https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch=$q&gsrnamespace=6&gsrlimit=50&prop=imageinfo&iiprop=url|size|extmetadata&iiurlwidth=360&format=json" > s.json
jq -r '.query.pages[] | "\(.index)\t\(.title)\t\(.imageinfo[0].width)x\(.imageinfo[0].height)\t\(.imageinfo[0].extmetadata.DateTimeOriginal.value // "" | .[0:10])\t\(.imageinfo[0].extmetadata.LicenseShortName.value)\t\(.imageinfo[0].extmetadata.Artist.value // "" | gsub("<[^>]*>";"") | .[0:40])"' s.json | sort -n | tee $out/list.tsv
i=0; jq -r '.query.pages | to_entries | sort_by(.value.index) | .[].value.imageinfo[0].thumburl' s.json | while read u; do i=$((i+1)); curl -sS -A "$UA" -o $out/$(printf %02d $i).jpg "$u" || true; sleep 0.3; done
