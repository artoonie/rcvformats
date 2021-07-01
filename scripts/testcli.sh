# Ensures the cli tooling works - make sure any changes here
# are propagated to the documentation
set -e

rcvformats -h > /dev/null

compare () {
  if ! diff <(jq '.' $out) <(jq '.' $expected); then
    echo "Comparison failed - $out and $expected should be the same"
    exit -1
  fi
}

echo Testing convert
in=testdata/inputs/electionbuddy/standard-with-threshold.csv
out=/tmp/standard-with-threshold.json
expected=testdata/conversions/from-electionbuddy-with-threshold.json
rcvformats convert -i $in -o $out
compare

echo Testing adding transfers
in=testdata/inputs/ut-without-transfers/with-decimals.json
out=/tmp/with-transfers.json
expected=testdata/inputs/universal-tabulator/simple.json
rcvformats transfer -i $in -o $out
compare

echo Testing adding transfer as strings
in=testdata/inputs/ut-without-transfers/with-strings.json
out=/tmp/with-transfers.json
rcvformats transfer -i $in -o $out
# Here, we're not gonna compare - just verify it doesn't fail with the same data as strings

echo "Success"
