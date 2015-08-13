#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import print_function

import logging
logger = logging.getLogger('feature_location')

import common
from common import *


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

        collect_info(project, repos, queries, goldsets, changeset_corpus, release_corpus)

        if 'release' in project.source and results['release'] is None:
            results['release'] = run_basic(project, release_corpus, release_corpus,
                                           queries, goldsets, 'release', names['release'])

        if 'changeset' in project.source and results['changeset'] is None:
            results['changeset'] = run_basic(project, changeset_corpus, release_corpus,
                                             queries, goldsets, 'changeset', names['changeset'])

        if 'temporal' in project.source and results['temporal'] is None:
            try:
                results['temporal'] = run_temporal(project, repos, changeset_corpus,
                                                   queries, goldsets, names['temporal'])
            except IOError:
                logger.info("Files needed for temporal evaluation not found. Skipping.")

    return results


def run_temporal_helper(project, repos, corpus, queries, goldsets):
    """
    This function runs the experiment in over time. That is, it stops whenever
    it reaches a commit linked with an issue/query. Will not work on all
    projects.
    """
    ids = load_ids(project)
    issue2git, git2issue = load_issue2git(project, ids)

    logger.info("Stopping at %d commits for %d issues", len(git2issue), len(issue2git))

    if project.model == "lda":
        model, model_fname = create_lda_model(project, None, corpus.id2word, 'temporal', use_level=False, force=True)

    if project.model == "lsi":
        model, model_fname = create_lsi_model(project, None, corpus.id2word, 'temporal', use_level=False, force=True)

    indices = list()
    ranks = dict()
    docs = list()
    corpus.metadata = True
    prev = 0

    # let's partition the corpus first
    for idx, docmeta in enumerate(corpus):
        doc, meta = docmeta
        sha, _ = meta
        if sha in git2issue:
            indices.append((prev, idx+1, sha))
            prev = idx

    logger.info('Created %d partitions of the corpus', len(indices))
    corpus.metadata = False

    for counter, index  in enumerate(indices):
        logger.info('At %d of %d partitions', counter, len(indices))
        start, end, sha = index
        docs = list()
        for i in xrange(start, end):
            docs.append(corpus[i])

        if project.model == "lda":
            model.update(docs,
                    #chunksize=project.chunksize,
                    offset=project.offset,
                    decay=project.decay)
        if project.model == "lsi":
            model.add_documents(docs)

        for qid in git2issue[sha]:
            logger.info('Getting ranks for query id %s', qid)
            # build a developer corpus of items *at this commit*
            # build a snapshot corpus of items *at this commit*
            try:
                other_corpus = create_release_corpus(project, repos, forced_ref=sha)
            except TaserError:
                continue

            query_topic = get_topics(model, queries, by_ids=[qid])
            doc_topic = get_topics(model, other_corpus)
            subranks = get_rank(goldsets, query_topic, doc_topic)
            if qid in subranks:
                if qid not in ranks:
                    ranks[qid] = list()

                rank = subranks[qid]
                ranks[qid].extend(rank)
            else:
                logger.info('Couldnt find qid %s', qid)


    model.save(model_fname)
    return ranks


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

                    goldsets[id_].update([item for kind, item in changes])

    logger.info("Returning %d goldsets", len(goldsets))
    return goldsets

