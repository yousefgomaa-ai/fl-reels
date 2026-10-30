# bash make.sh <dir> <music file>: frames, then a 1080p YouTube MP4 (voice + music under it).
set -e
d=$1; M=$2
node render.cjs $d
T=$(python3 -c "import json;print(json.load(open('$d/timeline.json'))['total'])")
ffmpeg -loglevel error -y -framerate 24 -i $d/frames/%05d.jpg -i $d/voice.mp3 -stream_loop -1 -i "$M" -filter_complex "[1:a]adelay=500:all=1,apad[n];[2:a]volume=0.10,afade=t=in:d=1.5,afade=t=out:st=$(python3 -c "print($T-2.5)"):d=2.5[m];[n][m]amix=inputs=2:duration=first:normalize=0[a]" -map 0:v -map '[a]' -c:v libx264 -preset medium -crf 22 -pix_fmt yuv420p -c:a aac -b:a 160k -t $T -movflags +faststart out-$d.mp4
rm -rf $d/frames; echo "$d done $T $(stat -c %s out-$d.mp4)"
