#!/bin/bash



runs="/mnt/volume-nyc1-01/thesis-data/runs"
logs="${runs}/logs"
mkdir -p ${logs}

function run {
    log_dest="${logs}/${1}-${2}.log"
    for i in $(seq 1 1); do
        data_dest="${runs}/${i}"
        mkdir -p ${data_dest}

        find data/${1} -name 'LDA*' -exec rm {} \; >> ${log_dest}
        find data/${1} -name '*.lda*' -exec rm {} \; >> ${log_dest}
        find data/${1} -name "*ranks*.csv.gz" -exec rm {} \; >> ${log_dest}

        echo "running flt ${@} ${i}"

        echo "" >> ${log_dest}
        echo "***********" >> ${log_dest}
        echo "running flt ${@} ${i}" >> ${log_dest}
        echo "***********" >> ${log_dest}
        date >> ${log_dest}
        echo "***********" >> ${log_dest}
        time cdi -v \
            --model lda \
            --experiment feature_location \
            --optimize_${2} \
            --source changeset \
            --name ${1} \
            --random-seed-value ${i} &>> ${log_dest}

        echo "running dit ${@} ${i}"

        echo "" >> ${log_dest}
        echo "***********" >> ${log_dest}
        echo "running dit ${@} ${i}" >> ${log_dest}
        echo "***********" >> ${log_dest}
        date >> ${log_dest}
        echo "***********" >> ${log_dest}
        time cdi -v \
            --model lda \
            --experiment triage \
            --optimize_${2} \
            --source changeset \
            --name ${1} \
            --random-seed-value ${i} &>> ${log_dest}

        find data/${1} -name "*ranks*.csv.gz" | cpio -pvdmB ${data_dest} >> ${log_dest}
    done
}

run "bookkeeper" "model"
run "mahout" "model"
run "openjpa" "model"
run "pig" "model"
run "tika" "model"
run "zookeeper" "model"

run "bookkeeper" "corpus"
run "mahout" "corpus"
run "openjpa" "corpus"
run "pig" "corpus"
run "tika" "corpus"
run "zookeeper" "corpus"
