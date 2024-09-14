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
