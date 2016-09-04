#!/bin/bash

TOKEN=`cat ${HOME}/digitalocean.token`

call(){
    HTTP_METHOD=$1
    OBJECT=$2
    curl -s -X $HTTP_METHOD \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        "https://api.digitalocean.com/v2/$OBJECT"
}

droplets=`call GET droplets`
addresses=`echo ${droplets} | python -m json.tool | \
    grep -E ip_address | awk '{print $2}' | sed -E "s/[^0-9.]//g"`

DATA_DIR=${HOME}/thesis-data

echo ${addresses}

echo "Copying from ${DATA_DIR}"
for each in ${addresses}; do
    echo ""
    echo "${each}"
    rsync -avz --include='*/' \
        --include='*ranks.csv.gz' \
        --include='*.log' \
        --exclude='*' \
        --prune-empty-dirs \
        -e ssh ${each}:${DATA_DIR} ${HOME}
done;

echo "Copying to local ./data"
rsync -avz --include='*/' \
    --include='*ranks.csv.gz' \
    --exclude='*' \
    --prune-empty-dirs \
    ${DATA_DIR}/runs/data data
