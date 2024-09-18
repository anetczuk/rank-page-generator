#!/bin/bash

set -eu


## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")


echo "running simple example"


OUT_DIR="$SCRIPT_DIR/rank_pages"

rm -fr "$OUT_DIR"


cd "$SCRIPT_DIR/../../src/"


DATA_PATH="$SCRIPT_DIR/model.xls"


python3 -m rankpagegenerator.main -la info \
								--data "$DATA_PATH"

if [[ $* == *--info* ]]; then
	# print only info
	exit 0
fi

python3 -m rankpagegenerator.main -la generate \
								--data "$DATA_PATH" \
								--outdir "$OUT_DIR"


echo -e "\n\nchecking links"

result=$(checklink -r -q "$OUT_DIR/index.html")
if [[ "$result" != "" ]]; then
	echo "broken links found:"
	echo "$result"
	exit 1
fi
# else: # empty string - no errors
echo "no broken links found"


## generate image from html
echo -e "\ntaking screenshots"
PAGE_PATH="$OUT_DIR/index.html"
if [ -f "$PAGE_PATH" ]; then
	OUT_IMG_PATH="$OUT_DIR/main-page.png"
	chromium --headless "file://$PAGE_PATH" --screenshot="$OUT_IMG_PATH"
	mogrify -trim "$OUT_IMG_PATH"
	convert -bordercolor \#EBEDEF -border 20 "$OUT_IMG_PATH" "$OUT_IMG_PATH"
	convert "$OUT_IMG_PATH" -strip "$OUT_IMG_PATH"
	exiftool -overwrite_original -all= "$OUT_IMG_PATH"

	OUT_IMG_PATH="$OUT_DIR/main-page-filter.png"
	chromium --headless "file://${PAGE_PATH}?horn=yes&wings=no" --screenshot="$OUT_IMG_PATH"
	mogrify -trim "$OUT_IMG_PATH"
	convert -bordercolor \#EBEDEF -border 20 "$OUT_IMG_PATH" "$OUT_IMG_PATH"
	convert "$OUT_IMG_PATH" -strip "$OUT_IMG_PATH"
	exiftool -overwrite_original -all= "$OUT_IMG_PATH"
fi

PAGE_PATH="$OUT_DIR/subpage/0.html"
if [ -f "$PAGE_PATH" ]; then
	OUT_IMG_PATH="$OUT_DIR/sub-page.png"
	chromium --headless "file://$PAGE_PATH" --screenshot="$OUT_IMG_PATH"
	mogrify -trim "$OUT_IMG_PATH"
	convert -bordercolor \#EBEDEF -border 20 "$OUT_IMG_PATH" "$OUT_IMG_PATH"
	convert "$OUT_IMG_PATH" -strip "$OUT_IMG_PATH"
	exiftool -overwrite_original -all= "$OUT_IMG_PATH"
fi


echo -e "\ngeneration completed"
