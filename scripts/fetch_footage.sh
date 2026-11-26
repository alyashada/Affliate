#!/usr/bin/env bash
# Download the 3 source videos from Google Drive and make upright 1080x1920 footage for the composition.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p raw video/assets/footage
ids=(1R5iEdgLNsJu_oLJw31NwhsM8mbM9iBrb 1VEz2wAlRhyYITdDPQXAxtdwqz1fXyxSP 1eWuDboU9x95LOhGdq_w2ccp5IETnSK1u)
for i in 1 2 3; do
  [ -f raw/clip$i.mp4 ] || curl -sSL -o raw/clip$i.mp4 "https://drive.usercontent.google.com/download?id=${ids[$((i-1))]}&export=download&confirm=t"
  ffmpeg -v error -y -i raw/clip$i.mp4 -an -vf "scale=1080:1920,fps=30" -c:v libx264 -preset fast -crf 20 -g 30 -movflags +faststart video/assets/footage/clip$i.mp4
done
