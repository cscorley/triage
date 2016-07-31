#!/bin/bash


runs="${HOME}/thesis-data/runs"
logs="${runs}/logs"
mkdir -p ${logs}

function run {
    for i in $(seq 1 50); do
        find data/${1} -name 'LDA*' -exec rm {} \;
        find data/${1} -name '*.lda*' -exec rm {} \;
        find data/${1} -name "*ranks*.csv.gz" -exec rm {} \;

        experiments=(feature_location triage)
        for experiment in ${experiments}; do
            log_dest="${logs}/${i}-${1}-${2}-${experiment}.log"
            echo "running ${experiment} ${@} ${i}"
            date >> ${log_dest}

            time cdi -v --model lda \
                --experiment ${experiment} \
                --source release \
                --source changeset \
                --name ${1} \
                --random-seed-value ${i} &>> ${log_dest}
        done

        find data/${1} -name "*ranks*.csv.gz" | cpio -pvdmB ${data_dest} >> ${log_dest}
    done
}

for project in ${@}; do
    run ${project}
done
