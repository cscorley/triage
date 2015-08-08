#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import print_function

import logging
logger = logging.getLogger('main')

from pprint import pprint

import click
import optunity
import numpy

import utils
import common
import triage
import feature_location


@click.command()
@click.option('-v', '--verbose', help="Enable verbose output", count=True)
@click.option('--force',         help="Overwrite existing data instead of reloading", is_flag=True)
@click.option('--optimize',      help="Find an optimal configuration for experiment", is_flag=True)
@click.option('--goldset',       help="Build a goldset for project (overrides other parameters)", is_flag=True)
@click.option('--release',       help="Run release evaluation", is_flag=True)
@click.option('--changeset',     help="Run changeset evaluation", is_flag=True)
@click.option('--temporal',      help="Run historical simulation", is_flag=True)
@click.option('--name',          help="Name of project to run experiment on")
@click.option('--version',       help="Version of project to run experiment on")
@click.option('--level',         help="Granularity level to run experiment on",
              default="file",    type=click.Choice(["file", "class", "method"]))
@click.option('--experiment',    help="Run selected experiment",
              default="triage",  type=click.Choice(["triage", "feature_location"]))
@click.option('--model',         help="Evaluate using selected model",
              default="lda",     type=click.Choice(["lsi", "lda", "hdp", "hpyp"]))
def cli(verbose, name, version, *args, **kwargs):
    logging.basicConfig(format='%(asctime)s : %(levelname)s : ' +
                        '%(name)s : %(funcName)s : %(message)s')

    if verbose > 1:
        logging.root.setLevel(level=logging.DEBUG)
    elif verbose == 1:
        logging.root.setLevel(level=logging.INFO)
    elif verbose == 0:
        logging.root.setLevel(level=logging.ERROR)

    lda_config = {
        'alpha': 'auto',
        'chunksize': 2000,
        'decay': 0.5,
        'eta': None,
        'iterations': 1000,
        'num_topics': 500,
        'offset': 1.0,
        'passes': 1,
    }

    kwargs.update({'lda_config': lda_config})
    kwargs.update({'lda_config_string': '-'.join([unicode(v) for k, v in sorted(lda_config.items())])})

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
            pars, aux = s.maximize(wrap(project))
            print("Parameters explored:", s.parameter_tuples)
            print("Optimal parameters:", pars)
            print("Aux info:", aux)
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

        project.lda_config.update(kwargs)
        p = project._replace(lda_config_string='-'.join([unicode(v) for k, v in sorted(project.lda_config.items())]))

        results['feature location'] = feature_location.run_experiment(p)

        return utils.calculate_mrr(num for num, _, _ in results['feature location']['release']['lda'])

    return inner

def do_science(a_first_rels, b_first_rels, ignore=False):
    # Build a dictionary with each of the results for stats.
    x, y = merge_first_rels(a_first_rels, b_first_rels, ignore=ignore)
    print(len(x), len(y))

    return { 'a_mrr': utils.calculate_mrr(x),
             'b_mrr': utils.calculate_mrr(y),
             'wilcoxon': scipy.stats.wilcoxon(x, y),
           }
    #print(prefix+' changeset mrr:', )
    #print(prefix+' release mrr:', )
    #print(prefix+' wilcoxon signedrank:', )
    #print(prefix+' ranksums:', scipy.stats.ranksums(x, y))
    #print(prefix+' mann-whitney:', scipy.stats.mannwhitneyu(x, y))
    #print('friedman:', scipy.stats.friedmanchisquare(x, y, x2, y2))

