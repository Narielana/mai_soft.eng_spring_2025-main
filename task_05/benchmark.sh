#!/bin/bash

DURATION=10s
HOST="http://localhost:8082"
USER_ID=1

USERNAME="admin"
PASSWORD="secret"

RESULTS_FILE="performance_results.txt"

echo "Getting authentication token..."
TOKEN_RESPONSE=$(curl -s -X POST "$HOST/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$USERNAME&password=$PASSWORD")

if command -v jq &> /dev/null; then
    ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')
else
    # Альтернативный вариант без jq
    ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
fi

if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" == "null" ]; then
    echo "Failed to get access token. Check your username and password."
    echo "Response: $TOKEN_RESPONSE"
    exit 1
fi

echo "Successfully obtained access token."
AUTH_HEADER="Authorization: Bearer $ACCESS_TOKEN"

echo "Performance Test Results" > $RESULTS_FILE
echo "=======================" >> $RESULTS_FILE
echo "Date: $(date)" >> $RESULTS_FILE
echo "" >> $RESULTS_FILE

run_test() {
    local endpoint=$1
    local description=$2
    local threads=$3
    local connections=$4
    
    echo "Testing: $description (Threads: $threads, Connections: $connections)" >> $RESULTS_FILE
    echo "Endpoint: $endpoint" >> $RESULTS_FILE
    echo "--------------------------------------" >> $RESULTS_FILE
    
    # Запускаем wrk и сохраняем результаты
    wrk -t$threads -c$connections -d$DURATION --latency -H "$AUTH_HEADER" $endpoint >> $RESULTS_FILE
    
    echo "" >> $RESULTS_FILE
    echo "" >> $RESULTS_FILE
}

echo "Warming up cache..."
curl -s -H "$AUTH_HEADER" "$HOST/users/list" > /dev/null
curl -s -H "$AUTH_HEADER" "$HOST/users/get?user_id=$USER_ID" > /dev/null

echo "## List Endpoint Tests" >> $RESULTS_FILE
echo "" >> $RESULTS_FILE

run_test "$HOST/users/list" "List with cache" 1 10
run_test "$HOST/users/list-no-cache" "List without cache" 1 10

run_test "$HOST/users/list" "List with cache" 5 10
run_test "$HOST/users/list-no-cache" "List without cache" 5 10

run_test "$HOST/users/list" "List with cache" 10 10
run_test "$HOST/users/list-no-cache" "List without cache" 10 10

echo "## Get Endpoint Tests" >> $RESULTS_FILE
echo "" >> $RESULTS_FILE

run_test "$HOST/users/get?user_id=$USER_ID" "Get with cache" 1 10
run_test "$HOST/users/get-no-cache?user_id=$USER_ID" "Get without cache" 1 10

run_test "$HOST/users/get?user_id=$USER_ID" "Get with cache" 5 10
run_test "$HOST/users/get-no-cache?user_id=$USER_ID" "Get without cache" 5 10

run_test "$HOST/users/get?user_id=$USER_ID" "Get with cache" 10 10
run_test "$HOST/users/get-no-cache?user_id=$USER_ID" "Get without cache" 10 10

echo "Tests completed. Results saved to $RESULTS_FILE"
