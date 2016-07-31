#!/bin/bash


runs="${HOME}/thesis-data/runs"
logs="${runs}/logs"
mkdir -p ${logs}

function run {
    log_dest="${logs}/${1}.log"
    for i in $(seq 1 50); do
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
        time cdi -v --model lda --experiment feature_location --source release --source changeset --name ${1} --random-seed-value ${i} &>> ${log_dest}

        echo "running dit ${@} ${i}"

        echo "" >> ${log_dest}
        echo "***********" >> ${log_dest}
        echo "running dit ${@} ${i}" >> ${log_dest}
        echo "***********" >> ${log_dest}
        date >> ${log_dest}
        echo "***********" >> ${log_dest}
        time cdi -v --model lda --experiment triage --source release --source changeset --name ${1} --random-seed-value ${i} &>> ${log_dest}

        find data/${1} -name "*ranks*.csv.gz" | cpio -pvdmB ${data_dest} >> ${log_dest}
    done
}

for project in ${@}; do
    run ${project}
done
