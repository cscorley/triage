#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import print_function

import logging
logger = logging.getLogger('feature_location')

import common
from common import *

from goldsets import build_goldset, load_goldset


def run_experiment(project):
    logger.info("Running project on %s", str(project))

    goldsets = create_goldsets(project)

    # check if ranks exist first -- save time by not loading corpora, etc

    results = dict()
    names = dict()

    for each in project.source:
        ranks, name = common.check_ranks(project, each, 'feature_location')
        names[each] = name

        if ranks:
            results[each] = get_frms(ranks, goldsets)
        else:
            results[each] = None

    if any([x is None for x in results.values()]):
        repos = load_repos(project)

        # create/load document lists
        queries = create_queries(project)
        ids = load_ids(project)

        # get corpora
        release_corpus = create_release_corpus(project, repos)
        changeset_corpus = create_corpus(project, repos, ChangesetCorpus, use_level=False)

        collect_info(project, queries, goldsets, changeset_corpus, release_corpus)

        if 'release' in project.source and results['release'] is None:
            fn = 'release-%s' % project.level
            result, train_perplexity, other_perplexity = run_basic(project,
                    release_corpus, release_corpus, queries, goldsets, fn,
                    names['release'])

            common.append_perplexity(project, train_perplexity, "release-feature_location-train-perplexity")
            common.append_perplexity(project, other_perplexity, "release-feature_location-other-perplexity")

            results['release'] = result

        if 'changeset' in project.source and results['changeset'] is None:
            fn = 'changeset-%s' % project.changeset_config_string
            result, train_perplexity, other_perplexity = run_basic(project,
                    changeset_corpus, release_corpus, queries, goldsets, fn,
                    names['changeset'])

            common.append_perplexity(project, train_perplexity, "changeset-feature_location-train-perplexity")
            common.append_perplexity(project, other_perplexity, "changeset-feature_location-other-perplexity")

            results['changeset'] = result
        if 'temporal' in project.source and results['temporal'] is None:
            results['temporal'] = run_temporal(project, repos, changeset_corpus,
                                                create_release_corpus,
                                                queries, goldsets, names['temporal'])

    return results


def create_goldsets(project):
    logger.info("Loading goldsets for project: %s", str(project))
    ids = load_ids(project)
    issue2git, git2issue = load_issue2git(project, ids)

    commit_golds = load_goldset(project) # lol naming

    goldsets = dict()
    for id_ in ids:
        if id_ in issue2git:
            shas = issue2git[id_]
            for sha in shas:
                if sha in commit_golds:
                    commit, changes = commit_golds[sha]
                    if id_ not in goldsets:
                        goldsets[id_] = set()

                    if project.level == 'file':
                        goldsets[id_].update([item for kind, item in changes if item.endswith(".java")])
                    else:
                        goldsets[id_].update([item for kind, item in changes])

    logger.info("Returning %d goldsets", len(goldsets))
    return goldsets

