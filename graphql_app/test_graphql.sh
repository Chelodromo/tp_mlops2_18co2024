#!/usr/bin/env bash
set -euo pipefail

GRAPHQL_URL="${GRAPHQL_URL:-http://127.0.0.1:8010/graphql}"

post() {
  local body="$1"
  curl -sS -H "Content-Type: application/json" -X POST "$GRAPHQL_URL" -d "$body"
}

assert_contains() {
  local haystack="$1"
  local needle="$2"
  echo "$haystack" | grep -q "$needle" || { 
    echo "ASSERT FAIL: no se encontró '$needle' en:"
    echo "$haystack"
    return 1
  }
}

echo "[test] reloadModel..."
OUT=$(post '{"query":"mutation{ reloadModel { status } }"}')
assert_contains "$OUT" '"status"'

echo "[test] modelInfo..."
OUT=$(post '{"query":"{ modelInfo { timestamp isLoaded features } }"}')
assert_contains "$OUT" '"isLoaded": true'
assert_contains "$OUT" '"features"'

echo "[test] predict (1 registro)..."
read -r -d '' ONE << 'JSON' || true
{
  "query": "mutation($x:WeatherData!){ predict(weatherData:$x){ probability } }",
  "variables": {
    "x": {
      "TempOut": 25, "DewPt": 10, "WSpeed": 12, "WHSpeed": 20,
      "Bar": 1010, "Rain": 0, "ET": 2.3, "WDirDeg": 180, "DateNum": 1723330000
    }
  }
}
JSON
OUT=$(post "$ONE")
assert_contains "$OUT" '"probability"'

echo "[test] predictBatch (2 registros)..."
read -r -d '' BATCH << 'JSON' || true
{
  "query": "mutation($xs:[WeatherData!]!){ predictBatch(weatherDataList:$xs){ predictions { date probability } } }",
  "variables": {
    "xs": [
      { "TempOut": 25, "DewPt": 15, "WSpeed": 5,  "WHSpeed": 12, "Bar": 1013, "Rain": 0, "ET": 1.1, "WDirDeg": 120, "DateNum": 1723330000 },
      { "TempOut": 10, "DewPt": 2,  "WSpeed": 12, "WHSpeed": 25, "Bar": 1000, "Rain": 1, "ET": 0.5, "WDirDeg": 80,  "DateNum": 1723330500 }
    ]
  }
}
JSON
OUT=$(post "$BATCH")
assert_contains "$OUT" '"predictions"'
assert_contains "$OUT" '"probability"'

echo "[test] ✅ todas las pruebas pasaron"
