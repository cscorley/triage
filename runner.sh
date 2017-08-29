#!/bin/bash


number_of_runs=1
runs="${HOME}/thesis-data/runs"
logs="${runs}/logs"
mkdir -p ${logs}

function run {
    for i in $(seq 1 ${number_of_runs}); do
        #experiments=(feature_location triage)
        experiments=(feature_location)
        for experiment in ${experiments[@]}; do
            log_dest="${logs}/${i}-${1}-run-${experiment}.log"
            echo "running ${experiment} ${@} ${i}"
            date >> ${log_dest}

            find data/${1} -name 'LDA*' -exec rm {} \;
            find data/${1} -name '*.lda*' -exec rm {} \;

            time cdi -v --model lda \
                --experiment ${experiment} \
                --source release \
                --source changeset \
                --level file \
                --name ${1} \
                --random-seed-value ${i} &>> ${log_dest}
        done

        find data -name "*ranks.csv.gz" | cpio -pvdmB ${runs} >> ${log_dest}
    done
}

for project in ${@}; do
    run ${project}
done
