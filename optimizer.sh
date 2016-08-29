#!/bin/bash



runs="${HOME}/thesis-data/runs"
logs="${runs}/logs"
mkdir -p ${logs}

function run {
    for i in $(seq 1 1); do
#        find data/${1} -name "*ranks*.csv.gz" -exec rm {} \;

        experiments=(feature_location triage)
        for experiment in ${experiments[@]}; do
            log_dest="${logs}/${i}-${1}-${2}-${experiment}.log"
            echo "running ${experiment} ${@} ${i}"
            date >> ${log_dest}

            # to perform a "fair" evaluation and make sure each of them start at
            # the same exact random state (including inferences) we need to
            # start fresh each time.
            #
            # in other words, lmao
            find data/${1} -name 'LDA*' -exec rm {} \;
            find data/${1} -name '*.lda*' -exec rm {} \;

            time cdi -v \
                --model lda \
                --experiment ${experiment} \
                --optimize_${2} \
                --source changeset \
                --name ${1} \
                --random-seed-value ${i} &>> ${log_dest}
        done

        find data -name "*ranks.csv.gz" | cpio -pvdmB ${runs} >> ${log_dest}
    done
}

for project in ${@}; do
    run ${project} "model"
    run ${project} "corpus"
done

