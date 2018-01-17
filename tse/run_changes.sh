#!/bin/bash

DATA=../data

echo "BookKeeper"
python3 changes.py $DATA/bookkeeper/changes-file.log.gz $DATA/bookkeeper/v4.3.0/changes-file-goldset.csv
echo "Mahout"
python3 changes.py $DATA/mahout/changes-file.log.gz $DATA/mahout/v0.10.0/changes-file-goldset.csv
echo "OpenJPA"
python3 changes.py $DATA/openjpa/changes-file.log.gz $DATA/openjpa/v2.3.0/changes-file-goldset.csv
echo "Pig"
python3 changes.py $DATA/pig/changes-file.log.gz $DATA/pig/v0.14.0/changes-file-goldset.csv
echo "Tika"
python3 changes.py $DATA/tika/changes-file.log.gz $DATA/tika/v1.8/changes-file-goldset.csv
echo "ZooKeeper"
python3 changes.py $DATA/zookeeper/changes-file.log.gz $DATA/zookeeper/v3.5.0/changes-file-goldset.csv

