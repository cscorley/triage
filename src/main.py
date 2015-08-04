#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import print_function

import logging
logger = logging.getLogger('main')

from pprint import pprint

import click

import common
import triage
import feature_location


@click.command()
@click.option('--verbose',          help="Enable verbose output",                             is_flag=True)
@click.option('--debug',            help="Enable debug output (very verbose)",                is_flag=True)
@click.option('--force',            help="Overwrite existing data instead of reloading",      is_flag=True)
@click.option('--optimize',         help="Find an optimal configuration for experiment",      is_flag=True)
@click.option('--triage',           help="Run feature location experiment",                   is_flag=True)
@click.option('--feature_location', help="Run feature location experiment",                   is_flag=True)
@click.option('--goldset',          help="Build a goldset (overrides other parameters)",      is_flag=True)
@click.option('--lda',              help="Evaluate using LDA",                                is_flag=True)
@click.option('--hdp',              help="Evaluate using HDP",                                is_flag=True)
@click.option('--hpyp',             help="Evaluate using HPYP",                               is_flag=True)
@click.option('--lsi',              help="Evaluate using LSI",                                is_flag=True)
@click.option('--temporal',         help="Run historical simulation",                         is_flag=True)
@click.option('--name',             help="Name of project to run experiment on")
@click.option('--version',          help="Version of project to run experiment on")
@click.option('--level',            help="Granularity level of project to run experiment on", default="file")
def cli(debug, verbose, name, version, *args, **kwargs):
    logging.basicConfig(format='%(asctime)s : %(levelname)s : ' +
                        '%(name)s : %(funcName)s : %(message)s')

    if debug:
        logging.root.setLevel(level=logging.DEBUG)
    elif verbose:
        logging.root.setLevel(level=logging.INFO)
    else:
        logging.root.setLevel(level=logging.ERROR)

    lda_defaults = {
        'num_topics': 500,
        'chunksize': 2000,
        'passes': 1,
        'iterations': 1000,
        'decay': 0.5,
        'offset': 1.0,
        'eta': None,
        'alpha': 'symmetric',
    }

    kwargs.update(lda_defaults)

    # load project info
    projects = common.load_projects(kwargs)
    results = dict()
    for project in projects:
        logging.basicConfig(format='%(asctime)s : %(levelname)s : ' +
                            project.name + " " + project.version +
                            '%(name)s : %(funcName)s : %(message)s')
        if name:
            name = name.lower()

            if name == project.name:
                if version and version != project.version:
                    continue

                if project.goldset:
                    build_goldset(project)
                else:
                    results[project.printable_name] = run_experiments(project)

                break # done, boom shakalaka
        elif project.goldset:
            build_goldset(project)
        else:
            results[project.printable_name] = run_experiments(project)


    pprint(results)

def run_experiments(project):
    results = dict()

    if project.triage:
        results['triage'] = triage.run_experiment(project)

    if project.feature_location:
        results['feature location'] = feature_location.run_experiment(project)

    return results
