#!/bin/bash
set -e
set -o pipefail
set -u

sr=16000
to=wav
num_channels=1

if [ $# != 2 ]; then
  echo "Usage: $(basename $0) <in:fn_audio> <out:dir_out>"
  echo "Info: converts an audio file in a directory to a wav file."
  echo ""
  echo "Args:"
  echo "  fn_audio		# Audio file to convert"
  echo "  dir_out		# Directory where converted audio file(s) will"
  echo "			  be saved."
  echo "Options:"
  echo "  --sr <sample rate>	# Sample rate to sample audio down to. ($sr Hz)"
  echo "  --to <audio type>	# Audio type to convert to, e.g wav | ogg | mp3 ($to)"
  echo "  --num-channels <nc>	# Number of channels to extract ($num_channels)"
  exit 1;
fi

fn=`readlink -vf $1`
dir_out=`readlink -vf $2`

media=0
dur=0

if [ `mediainfo $fn 2>&1 | awk '{print $1}' | grep "Audio" | wc -l` -gt 0 ]; then
  echo "Info: MediaFile found: [$fn]"
  media=1
  ext=`echo $fn | awk -F '.' '{print $NF}'`
  bn=`echo $fn | awk -F '/' '{print $NF}' | sed "s/\.${ext}$//g"`
  mkdir -p $dir_out

  # TODO: check if it already exists, warn if it does
  if [ $to == "wav" ]; then
    ffmpeg -loglevel panic -i $fn -acodec pcm_s16le -ac $num_channels -ar $sr $dir_out/$bn.$to -y #>& /tmp/tmp.log
  else
    ffmpeg -loglevel panic -i $fn -ac $num_channels -ar $sr $dir_out/$bn.$to 
  fi

  # get duration
  dur=`soxi -D $dir_out/$bn.$to`

  rm $dir_out/$bn.$to
else
  echo "Warning: not a media file: [$fn]"
fi



echo "Info [`date`]: Done! $(basename $0)"
echo $fn.txt
echo $media > $fn.txt
echo $dur >> $fn.txt