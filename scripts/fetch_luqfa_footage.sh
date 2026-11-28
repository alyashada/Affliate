#!/usr/bin/env bash
# Re-download the Luqfa source video from Google Drive and make the upright 1080x1920 footage
# used by videos/luqfa-lotion and videos/luqfa-lotion-2 (the file is saved landscape, so rotate it).
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p raw2 videos/luqfa-lotion/assets/footage videos/luqfa-lotion-2/assets/footage
[ -f raw2/video.mp4 ] || curl -sSL -o raw2/video.mp4 "https://drive.usercontent.google.com/download?id=12_oi7-WjpfhmbZ_OWmsVTcSFXsF6EuRp&export=download&confirm=t"
ffmpeg -v error -y -i raw2/video.mp4 -an -vf "transpose=1,scale=1080:1920,fps=30" -c:v libx264 -preset fast -crf 20 -g 30 -movflags +faststart videos/luqfa-lotion/assets/footage/clip1.mp4
cp videos/luqfa-lotion/assets/footage/clip1.mp4 videos/luqfa-lotion-2/assets/footage/clip1.mp4
