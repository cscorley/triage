#!/bin/bash

TOKEN=`cat ${HOME}/digitalocean.token`

api(){
    HTTP_METHOD=$1
    OBJECT=$2
    curl -s -X $HTTP_METHOD \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        "https://api.digitalocean.com/v2/$OBJECT"
}

check(){
    each=${1}
    echo ""
    echo "${each}"
    result=`ssh ${each} "ps au | grep python"`
    echo "\"${result}\""
    if [ -z "${result}" ]; then
        echo "No Python process found running on ${each}, dropping into shell."
        ssh ${each}
    fi
    echo ""
}

droplets=`api GET droplets`
addresses=`echo ${droplets} | python -m json.tool | \
    grep -E ip_address | awk '{print $2}' | sed -E "s/[^0-9.]//g"`

echo ${addresses}
for each in ${addresses}; do
    check ${each}
done

#check twoism.meow
