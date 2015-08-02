#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import print_function

import logging
logger = logging.getLogger('main')

import click

import common
import triage


@click.command()
@click.option('--verbose', is_flag=True)
@click.option('--debug', is_flag=True)
@click.option('--force', is_flag=True)
@click.option('--temporal', is_flag=True)
@click.option('--optimize', is_flag=True)
@click.option('--triage', is_flag=True)
@click.option('--feature_location', is_flag=True)
@click.option('--goldset', is_flag=True)
@click.option('--lda', is_flag=True)
@click.option('--lsi', is_flag=True)
@click.option('--name', help="Name of project to run experiment on")
@click.option('--version', help="Version of project to run experiment on")
@click.option('--level', default="file", help="Granularity level of project to run experiment on")
@click.option('--num_topics', default=500, type=click.INT)
@click.option('--chunksize', default=2000, type=click.INT)
@click.option('--passes', default=1, type=click.INT)
@click.option('--iterations', default=1000, type=click.INT)
@click.option('--decay', default=0.5, type=click.FLOAT)
@click.option('--offset', default=1.0, type=click.FLOAT)
@click.option('--eta', type=click.FLOAT)
@click.option('--alpha', default='symmetric')
def cli(debug, verbose, name, version, goldset,  *args, **kwargs):
    logging.basicConfig(format='%(asctime)s : %(levelname)s : ' +
                        '%(name)s : %(funcName)s : %(message)s')

    if debug:
        logging.root.setLevel(level=logging.DEBUG)
    elif verbose:
        logging.root.setLevel(level=logging.INFO)
    else:
        logging.root.setLevel(level=logging.ERROR)

    # load project info
    projects = common.load_projects(kwargs)
    for project in projects:
        if name:
            name = name.lower()

            if name == project.name:
                if version and version != project.version:
                    continue

                if goldset:
                    build_goldset(project)
                else:
                    run_experiments(project)

                return # done, boom shakalaka
        elif goldset:
            build_goldset(project)
        else:
            run_experiments(project)

def run_experiments(project):
    if project.triage:
        print(triage.run_experiment(project))

    if project.feature_location:
        print(feature_location.run_experiment(project))
