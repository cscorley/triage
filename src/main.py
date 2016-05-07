#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import print_function, division

import logging
logger = logging.getLogger('main')

import coloredlogs

import csv
import os
import os.path
from pprint import pprint

import click
import optunity
import numpy
import scipy

import utils
import common
import goldsets
import triage
import feature_location


@click.command()
@click.option('--verbose', '-v',
              help='Enable verbose output',
              count=True)
@click.option('--force',
              help='Overwrite existing data instead of reloading',
              is_flag=True)
@click.option('--optimize_model',
              help='Find an optimal configuration for experiment',
              is_flag=True)
@click.option('--optimize_corpus',
              help='Find an optimal corpus for experiment',
              is_flag=True)
@click.option('--goldset',
              help='Build a goldset for project (overrides other parameters)',
              is_flag=True)
@click.option('--name',
              help='Name of project to run experiment on')
@click.option('--version',
              help='Version of project to run experiment on')
@click.option('--source',
              help='Run experiment on selected source',
              type=click.Choice(['release', 'changeset', 'temporal']),
              default=['release'],
              multiple=True)
@click.option('--level',
              help='Granularity level to run experiment on',
              type=click.Choice(['file', 'class', 'method']),
              default='file')
@click.option('--experiment',
              help='Run selected experiment',
              type=click.Choice(['triage', 'feature_location']),
              default='triage')
@click.option('--model',
              help='Evaluate using selected model',
              type=click.Choice(['lsi', 'lda', 'hdp', 'hpyp']),
              default='lda')
@click.option('--use-random-seed',
              is_flag=True)
def cli(verbose, name, version, *args, **kwargs):

    if not kwargs['use_random_seed']:
        numpy.random.seed(128169) # '💩'

    coloredlogs.install()

    if verbose > 1:
        coloredlogs.set_level(level=logging.DEBUG)
    elif verbose == 1:
        coloredlogs.set_level(level=logging.INFO)
    elif verbose == 0:
        coloredlogs.set_level(level=logging.ERROR)

    model_config, model_config_string = get_default_model_config(kwargs)
    changeset_config, changeset_config_string = get_default_changeset_config()

    kwargs.update({'changeset_config': changeset_config,
                   'changeset_config_string': changeset_config_string})

    kwargs.update({'model_config': model_config,
                   'model_config_string': model_config_string})

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
        if project.goldset:
            goldsets.build_goldset(project)
        elif project.optimize_model:
            optimize_model(project)
        elif project.optimize_corpus:
            optimize_corpus(project)
        else:
            pn = project.printable_name
            firstrels[pn] = run_experiments(project)
            if pn not in mrr:
                mrr[pn] = dict()

            for source in project.source:
                mrr[pn][source] = utils.calculate_mrr(num for num, _, _ in firstrels[pn][source])

    pprint(mrr)

def get_default_changeset_config():
    changeset_config = {
        'include_additions': True,
        'include_context': True,
        'include_message': False,
        'include_removals': True,
    }

    changeset_config_string = '-'.join([unicode(v) for k, v in sorted(changeset_config.items())])

    return changeset_config, changeset_config_string


def get_default_model_config(kwargs):
    if kwargs['model'] == 'lda':
        model_config = {
            'num_topics': 500,
            'alpha': 1/500,
            'eta': 1/500,
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

    model_config_string =  '-'.join([unicode(v) for k, v in sorted(model_config.items())])

    return model_config, model_config_string

def run_experiments(project):
    results = dict()

    if project.experiment == 'triage':
        results = triage.run_experiment(project)
    elif project.experiment == 'feature_location':
        results = feature_location.run_experiment(project)

    return results

def set_optimized_params(project, params):
    for each in project.source:
        path = os.path.join(project.full_path, 'optimized-model-%s-%s.csv' % (each, project.experiment))
        if os.path.exists(path):
            with open(path) as f:
                best_score = 0.0
                for row in csv.reader(f):
                    score, alpha_base, eta_base, num_topics = row
                    if score > best_score:
                        params['num_topics'] = num_topics
                        params['alpha'] = alpha_base / num_topics
                        params['eta'] = eta_base / num_topics


def optimize_model(project):
    # fix params here
    params = dict()
    if project.model == 'lda':
        params = {
            'model_base_alpha': ['auto', 1, 2, 5],
            'model_base_eta': ['auto', 1, 2, 5],
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
        s = optunity.solvers.GridSearch(**params)
        f = wrap(project, each)
        pars, aux = s.maximize(f)
        print("Parameters explored:", s.parameter_tuples)
        print("Optimal parameters:", pars)
        print("Aux info:", aux)
        # print("Call log:", f.call_log)
        log_dict = f.call_log.to_dict()
        path = os.path.join(project.full_path, 'optimized-model-%s-%s.csv' % (each, project.experiment))
        print("Writing full call log to", path)

        header = ['score'] + list(log_dict['args'].keys())
        items = list(zip(log_dict['values'], *log_dict['args'].values()))

        with open(path, 'w') as output:
            writer = csv.writer(output)
            writer.writerow(header)
            writer.writerows(items)

def optimize_corpus(project):
    # fix params here
    params = {'changeset_include_message': [True, False],
              'changeset_include_additions': [True, False],
              'changeset_include_removals': [True, False],
              'changeset_include_context': [True, False],
    }

    for each in project.source:
        s = optunity.solvers.GridSearch(**params)
        f = wrap(project, each)
        pars, aux = s.maximize(f)
        print("Parameters explored:", s.parameter_tuples)
        print("Optimal parameters:", pars)
        print("Aux info:", aux)
        # print("Call log:", f.call_log)
        log_dict = f.call_log.to_dict()
        path = os.path.join(project.full_path, 'optimized-corpus-%s-%s.csv' % (each, project.experiment))
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
                if value == 'auto':
                    project.model_config[new_arg] = value
                else:
                    project.model_config[new_arg] = float(value) / float(kwargs['num_topics'])
            else:
                project.model_config[arg] = value

        if not any(project.changeset_config.values()):
            return 0.0

        p = project._replace(model_config_string='-'.join([unicode(v) for k, v in sorted(project.model_config.items())]),
                             changeset_config_string='-'.join([unicode(v) for k, v in sorted(project.changeset_config.items())]))

        results = dict()

        if project.experiment == 'triage':
            results = triage.run_experiment(p)
        elif project.experiment == 'feature_location':
            results = feature_location.run_experiment(p)

        return utils.calculate_mrr(num for num, _, _ in results[source])

    return inner

def do_science(a_first_rels, b_first_rels, ignore=False):
    # Build a dictionary with each of the results for stats.
    x, y = common.merge_first_rels(a_first_rels, b_first_rels, ignore=ignore)
    print(len(x), len(y))

    return { 'a_mrr': utils.calculate_mrr(x),
             'b_mrr': utils.calculate_mrr(y),
             'wilcoxon': scipy.stats.wilcoxon(x, y),
           }
