#!/bin/bash

set -eu


## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")


echo "running simple example"


OUT_DIR="$SCRIPT_DIR/rank_pages"

rm -fr "$OUT_DIR"


cd "$SCRIPT_DIR/../../src/"


python3 -m rankpagegenerator.main -la generate \
								--data "$SCRIPT_DIR/model.xls" \
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
