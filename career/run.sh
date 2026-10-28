set -e
cd "$(dirname "$0")/work"
M=../../music/$(ls ../../music | sort | sed -n 2p)
for p in "$@"; do
  (cd $p && DIR=$p node ../render.cjs)
  T=$(python3 -c "import json;print(round(json.load(open('$p/timeline.json'))['total'],2))")
  ffmpeg -loglevel error -y -framerate 30 -i $p/frames/%05d.jpg -i $p/voice.mp3 -stream_loop -1 -i "$M" -filter_complex "[0:v]fps=24[v];[1:a]adelay=500:all=1,apad[n];[2:a]volume=0.13,afade=t=in:d=1,afade=t=out:st=$(python3 -c "print($T-2)"):d=2[m];[n][m]amix=inputs=2:duration=first:normalize=0[a]" -map '[v]' -map '[a]' -c:v libx264 -preset slow -crf 30 -tune film -pix_fmt yuv420p -c:a aac -b:a 96k -t $T -movflags +faststart ../out/$p.mp4
  echo "$p done $T $(stat -c %s ../out/$p.mp4)"
done
