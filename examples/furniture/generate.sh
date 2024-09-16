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
	chromium --headless "file://$PAGE_PATH" --screenshot=$OUT_DIR/main-page.png
	chromium --headless "file://${PAGE_PATH}?num_of_legs=3&back=yes" --screenshot=$OUT_DIR/main-page-filter.png
fi
PAGE_PATH="$OUT_DIR/pages/0.html"
if [ -f "$PAGE_PATH" ]; then
	chromium --headless "file://$PAGE_PATH" --screenshot=$OUT_DIR/sub-page.png
fi


echo -e "\ngeneration completed"
