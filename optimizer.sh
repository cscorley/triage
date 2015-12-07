#!/bin/bash


runs="~/runs"
logs="~/runs/logs"
mkdir -p ${logs}

function run {
    log_dest="${logs}/${1}.log"
    for i in $(seq 1 100); do
        data_dest="${runs}/${i}"
        mkdir -p ${data_dest}

        find data/${1} -name 'LDA*' -exec rm {} \; >> ${log_dest}
        find data/${1} -name '*.lda*' -exec rm {} \; >> ${log_dest}
        find data/${1} -name "*ranks*.csv.gz" -exec rm {} \; >> ${log_dest}

        echo "running flt ${1} ${i}"

        echo "" >> ${log_dest}
        echo "***********" >> ${log_dest}
        echo "running flt" >> ${log_dest}
        echo "***********" >> ${log_dest}
        date >> ${log_dest}
        echo "***********" >> ${log_dest}
        time cdi -v --model lda --experiment feature_location --optimize_model --source changeset --name ${1} &>> ${log_dest}

        echo "running dit ${1} ${i}"

        echo "" >> ${log_dest}
        echo "***********" >> ${log_dest}
        echo "running dit" >> ${log_dest}
        echo "***********" >> ${log_dest}
        date >> ${log_dest}
        echo "***********" >> ${log_dest}
        time cdi -v --model lda --experiment triage --optimize_model --source changeset --name ${1} &>> ${log_dest}

        find data/${1} -name "*ranks*.csv.gz" | cpio -pvdmB ${data_dest} >> ${log_dest}
    done
}

run "bookkeeper" &
run "mahout" &
run "openjpa" &
run "pig" &
run "tika" &
run "zookeeper"
