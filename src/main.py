#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import print_function

import logging
logger = logging.getLogger('main')

import csv
import os
import os.path
from pprint import pprint

import click
import optunity
import numpy

import utils
import common
import goldsets
import triage
import feature_location


@click.command()
@click.option('--verbose', '-v',
              help="Enable verbose output",
              count=True)
@click.option('--force',
              help="Overwrite existing data instead of reloading",
              is_flag=True)
@click.option('--optimize',
              help="Find an optimal configuration for experiment",
              is_flag=True)
@click.option('--goldset',
              help="Build a goldset for project (overrides other parameters)",
              is_flag=True)
@click.option('--name',
              help="Name of project to run experiment on")
@click.option('--version',
              help="Version of project to run experiment on")
@click.option('--source',
              help="Run experiment on selected source",
              type=click.Choice(["release", "changeset", "temporal"]),
              default="release",
              multiple=True)
@click.option('--level',
              help="Granularity level to run experiment on",
              type=click.Choice(["file", "class", "method"]),
              default="file")
@click.option('--experiment',
              help="Run selected experiment",
              type=click.Choice(["triage", "feature_location"]),
              default="triage")
@click.option('--model',
              help="Evaluate using selected model",
              type=click.Choice(["lsi", "lda", "hdp", "hpyp"]),
              default="lda")
def cli(verbose, name, version, *args, **kwargs):
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(name)s : %(funcName)s : %(message)s')

    if verbose > 1:
        logging.root.setLevel(level=logging.DEBUG)
    elif verbose == 1:
        logging.root.setLevel(level=logging.INFO)
    elif verbose == 0:
        logging.root.setLevel(level=logging.ERROR)

    if kwargs['model'] == 'lda':
        model_config = {
            'num_topics': 500,
            'alpha': 'auto',
            'eta': 'auto',
            'decay': 0.5,
            'offset': 1.0,
            'iterations': 1000,
            'passes': 1,
            'max_bound_iterations': 1000, # special
            'algorithm': 'batch', # special
        }
    elif kwargs['model'] == 'hdp':
        model_config = {
            'K': 15,
            'T': 150,
            'alpha': 1,
            'chunksize': 256,
            'eta': 0.01,
            'gamma': 1,
            'kappa': 1.0,
            'scale': 1.0,
            'tau': 64.0,
        }
    else:
        model_config = {}

    changeset_config = {
        'include_additions': True,
        'include_context': True,
        'include_message': False,
        'include_removals': True,
    }

    kwargs.update({'changeset_config': changeset_config})
    kwargs.update({'changeset_config_string': '-'.join([unicode(v) for k, v in sorted(changeset_config.items())])})

    kwargs.update({'model_config': model_config})
    kwargs.update({'model_config_string': '-'.join([unicode(v) for k, v in sorted(model_config.items())])})

    # load project info
    projects = common.load_projects(kwargs)

    if name:
        name = name.lower()
        projects = [x for x in projects if x.name == name]

    if version:
        version = version.lower()
        projects = [x for x in projects if x.version == version]


    mrr = dict()
    firstrels = dict()
    for project in projects:
        logging.basicConfig(format='%(asctime)s : %(levelname)s : ' +
                            project.printable_name +
                            '%(name)s : %(funcName)s : %(message)s')

        if project.goldset:
            goldsets.build_goldset(project)
        elif project.optimize:
            run_optimization(project)
        else:
            pn = project.printable_name
            firstrels[pn] = run_experiments(project)
            if pn not in mrr:
                mrr[pn] = dict()

            for source in project.source:
                mrr[pn][source] = utils.calculate_mrr(num for num, _, _ in firstrels[pn][source])

    pprint(mrr)

def run_experiments(project):
    results = dict()

    if project.experiment == 'triage':
        results = triage.run_experiment(project)
    elif project.experiment == 'feature_location':
        results = feature_location.run_experiment(project)

    return results

def run_optimization(project):
    # fix params here
    params = dict()
    if project.model == 'lda':
        params = {
            'model_base_alpha': [1, 2, 5],
            'model_base_eta': [1, 2, 5],
            'num_topics': [100, 200, 500],
        # campbell-etal
            #'alpha': [1.0/pow(2, x) for x in range(11)] + ['auto'],
            #'eta': [1.0/pow(2, x) for x in range(11)] + ['auto'],
            #'num_topics': [int(pow(2, x)) for x in range(3, 10)],
        # panichella-etal_2013a uses:
            #'num_topics': list(range(50, 501, 50)),
            #'alpha': [float(x) / 10 for x in range(1, 11, 1)] + ['auto', 'symmetric'],
            #'eta': [float(x) / 10 for x in range(1, 11, 1)] + ['auto', None], # here, none is the same as 'symmetric'
        }
    elif project.model == 'hdp':
        params = {
            'K': [15, 20],
            'T': [150, 200],
        }


    for each in project.source:
        if each == 'changeset' or each == 'temporal':
            params.update({
                'changeset_include_message': [True, False],
                'changeset_include_additions': [True, False],
                'changeset_include_removals': [True, False],
                'changeset_include_context': [True, False],
            })

        s = optunity.solvers.GridSearch(**params)
        f = wrap(project, each)
        pars, aux = s.maximize(f)
        print("Parameters explored:", s.parameter_tuples)
        print("Optimal parameters:", pars)
        print("Aux info:", aux)
        # print("Call log:", f.call_log)
        log_dict = f.call_log.to_dict()
        path = os.path.join(project.full_path, 'optimized-%s-%s.csv' % (each, project.experiment))
        print("Writing full call log to", path)

        header = ['score'] + list(log_dict['args'].keys())
        items = list(zip(log_dict['values'], *log_dict['args'].values()))

        with open(path, 'w') as output:
            writer = csv.writer(output)
            writer.writerow(header)
            writer.writerows(items)


def wrap(project, source):
    """Take in a project and configuration, return function that runs experiment with that config"""

    @optunity.functions.logged
    def inner(*args, **kwargs):
        for arg, value in kwargs.items():
            if arg.startswith('changeset_'):
                new_arg = arg[len('changeset_'):]
                project.changeset_config[new_arg] = value
            elif arg.startswith('model_base_'):
                new_arg = arg[len('model_base_'):]
                assert 'num_topics' in kwargs
                project.model_config[new_arg] = float(value) / float(kwargs['num_topics'])
            else:
                project.model_config[arg] = value

        if not any(project.changeset_config.values()):
            return 0.0

        p = project._replace(model_config_string='-'.join([unicode(v) for k, v in sorted(project.model_config.items())]),
                             changeset_config_string='-'.join([unicode(v) for k, v in sorted(project.changeset_config.items())]))

        assert p.model_config_string != project.model_config_string or p.changeset_config_string != project.changeset_config_string 
        results = dict()

        if project.experiment == 'triage':
            results = triage.run_experiment(p)
        elif project.experiment == 'feature_location':
            results = feature_location.run_experiment(p)

        return utils.calculate_mrr(num for num, _, _ in results[source])

    return inner

def do_science(a_first_rels, b_first_rels, ignore=False):
    # Build a dictionary with each of the results for stats.
    x, y = merge_first_rels(a_first_rels, b_first_rels, ignore=ignore)
    print(len(x), len(y))

    return { 'a_mrr': utils.calculate_mrr(x),
             'b_mrr': utils.calculate_mrr(y),
             'wilcoxon': scipy.stats.wilcoxon(x, y),
           }

