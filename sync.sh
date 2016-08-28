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
VOLUME="volume-nyc1-01"

echo ${addresses}
for each in ${addresses}; do
    mounts=`ssh ${each} "mount | grep ${VOLUME}"`
    mounts=$(echo ${mounts})
    echo "${each} mounts='${mounts}'"
    if [ ! -z "${mounts}" ]; then
        echo "Found mounts. Copying."
        rsync -avz -e ssh ${each}:/mnt/${VOLUME}/thesis-data ${HOME}
    fi
    echo ""
done;

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

echo "Copying from local ./data"
rsync -avz --include='*/' \
    --include='*ranks.csv.gz' \
    --include='*.log' \
    --exclude='*' \
    --prune-empty-dirs \
    data ${DATA_DIR}/runs/
