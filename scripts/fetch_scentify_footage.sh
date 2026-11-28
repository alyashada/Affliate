#!/usr/bin/env bash
# Re-download the two Scentify videos from Google Drive and make upright 1080x1920 footage (saved landscape → rotate).
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p raw3 videos/scentify/assets/footage
ids=(1Jmjrd8o0vRVyaT_abBA7cDG_NgGxW0nF 1E6H3v1-Igm-YCnCxbK5bxVf0cxE5b7H5)
for i in 1 2; do
  [ -f raw3/clip$i.mp4 ] || curl -sSL -o raw3/clip$i.mp4 "https://drive.usercontent.google.com/download?id=${ids[$((i-1))]}&export=download&confirm=t"
  ffmpeg -v error -y -i raw3/clip$i.mp4 -an -vf "transpose=1,scale=1080:1920,fps=30" -c:v libx264 -preset fast -crf 20 -g 30 -movflags +faststart videos/scentify/assets/footage/clip$i.mp4
done
