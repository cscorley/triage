#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import print_function

import logging
logger = logging.getLogger('main')

from pprint import pprint

import click
import optunity
import numpy

import common
import triage
import feature_location


@click.command()
@click.option('-v', '--verbose',    help="Enable verbose output",                        count=True)
@click.option('--force',            help="Overwrite existing data instead of reloading", is_flag=True)
@click.option('--optimize',         help="Find an optimal configuration for experiment", is_flag=True)
@click.option('--triage',           help="Run feature location experiment",              is_flag=True)
@click.option('--feature_location', help="Run feature location experiment",              is_flag=True)
@click.option('--goldset',          help="Build a goldset (overrides other parameters)", is_flag=True)
@click.option('--lda',              help="Evaluate using LDA",                           is_flag=True)
@click.option('--hdp',              help="Evaluate using HDP",                           is_flag=True)
@click.option('--hpyp',             help="Evaluate using HPYP",                          is_flag=True)
@click.option('--lsi',              help="Evaluate using LSI",                           is_flag=True)
@click.option('--temporal',         help="Run historical simulation",                    is_flag=True)
@click.option('--release',          help="Run release evaluation",                       is_flag=True)
@click.option('--changeset',        help="Run changeset evaluation",                     is_flag=True)
@click.option('--name',             help="Name of project to run experiment on")
@click.option('--version',          help="Version of project to run experiment on")
@click.option('--level',            help="Granularity level to run experiment on",
              default="file",       type=click.Choice(["file", "class", "method"]))
def cli(verbose, name, version, *args, **kwargs):
    logging.basicConfig(format='%(asctime)s : %(levelname)s : ' +
                        '%(name)s : %(funcName)s : %(message)s')

    if verbose > 1:
        logging.root.setLevel(level=logging.DEBUG)
    elif verbose == 1:
        logging.root.setLevel(level=logging.INFO)
    elif verbose == 0:
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

    if name:
        name = name.lower()
        projects = [x for x in projects if x.name == name]

    if version:
        version = version.lower()
        projects = [x for x in projects if x.version == version]


    results = dict()
    for project in projects:
        logging.basicConfig(format='%(asctime)s : %(levelname)s : ' +
                            project.printable_name +
                            '%(name)s : %(funcName)s : %(message)s')

        if project.goldset:
            build_goldset(project)
        elif project.optimize:
            # fix params here
            # panichella-etal_2013a uses:
            K = numpy.arange(50, 501, 50)
            alpha = numpy.arange(0.1, 1.1, 0.1)
            eta = numpy.arange(0.1, 1.1, 0.1)
            # we use the +1 on the bound because range is [a, jerk)

            s = optunity.solvers.GridSearch(num_topics=K, alpha=alpha, eta=eta)
            print(s.parameter_tuples)
            pars, opt = s.maximize(wrap(project))
            print(pars)
            print(opt)
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

def wrap(project):
    """Take in a project and configuration, return function that runs experiment with that config"""

    def inner(*args, **kwargs):
        results = dict()
        p = project._replace(**kwargs)

        results['feature location'] = feature_location.run_experiment(p)

        return results['feature location']['basic_lda']['b_mrr']

    return inner
