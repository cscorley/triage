#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import print_function

import logging
logger = logging.getLogger('feature_location')

from common import *

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

def run_experiment(project):
    logger.info("Running project on %s", str(project))

    repos = load_repos(project)

    # create/load document lists
    queries = create_queries(project)
    goldsets = create_goldsets(project)
    ids = load_ids(project)

    ownership = build_ownership(project, repos)

    # get corpora
    changeset_corpus = create_corpus(project, repos, ChangesetCorpus, use_level=False)
    release_corpus = create_release_corpus(project, repos)

    collect_info(project, repos, queries, goldsets, changeset_corpus, release_corpus)

    release_results = run_basic(project, release_corpus, release_corpus,
                                queries, goldsets, 'Release')

    changeset_results = run_basic(project, changeset_corpus, release_corpus,
                                  queries, goldsets, 'Changeset')

    results = dict()

    if project.temporal:
        try:
            temporal_lda, temporal_lsi = run_temporal(project, repos,
                                                      changeset_corpus, queries,
                                                      goldsets)
        except IOError:
            logger.info("Files needed for temporal evaluation not found. Skipping.")
        else:
            if project.lda:
                results['temporal_lda'] = do_science(temporal_lda, changeset_lda, ignore=True)
            if project.lsi:
                results['temporal_lsi'] = do_science(temporal_lsi, changeset_lsi, ignore=True)

    # do this last so that the results are printed together
    if project.lda:
        results['basic_lda'] = do_science(changeset_results['lda'], ownership_results['lda'])

    if project.lsi:
        results['basic_lsi'] = do_science(changeset_results['lsi'], ownership_results['lsi'])

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

    if project.lda:
        lda, lda_fname = create_lda_model(project, None, corpus.id2word,
                                        'Temporal', use_level=False, force=True)

    if project.lsi:
        lsi, lsi_fname = create_lsi_model(project, None, corpus.id2word,
                                        'Temporal', use_level=False, force=True)

    indices = list()
    lda_ranks = dict()
    lsi_ranks = dict()
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

        if project.lda:
            lda.update(docs,
                    #chunksize=project.chunksize,
                    offset=project.offset,
                    decay=project.decay)
        if project.lsi:
            lsi.add_documents(docs)

        for qid in git2issue[sha]:
            logger.info('Getting ranks for query id %s', qid)
            # build a developer corpus of items *at this commit*
            # build a snapshot corpus of items *at this commit*
            try:
                other_corpus = create_release_corpus(project, repos, forced_ref=sha)
            except TaserError:
                continue

            # do LDA magic
            if project.lda:
                lda_query_topic = get_topics(lda, queries, by_ids=[qid])
                lda_doc_topic = get_topics(lda, other_corpus)
                lda_subranks = get_rank(goldsets, lda_query_topic, lda_doc_topic)
                if qid in lda_subranks:
                    if qid not in lda_ranks:
                        lda_ranks[qid] = list()

                    rank = lda_subranks[qid]
                    lda_ranks[qid].extend(rank)
                else:
                    logger.info('Couldnt find qid %s', qid)

            # do LSI magic
            if project.lsi:
                lsi_query_topic = get_topics(lsi, queries, by_ids=[qid])
                lsi_doc_topic = get_topics(lsi, other_corpus)
                lsi_subranks = get_rank(goldsets, lsi_query_topic, lsi_doc_topic)
                if qid in lsi_subranks:
                    if qid not in lsi_ranks:
                        lsi_ranks[qid] = list()

                    rank = lsi_subranks[qid]
                    lsi_ranks[qid].extend(rank)
                else:
                    logger.info('Couldnt find qid %s', qid)

    lda_rels = list()
    if project.lda:
        lda.save(lda_fname)
        write_ranks(project, 'temporal', lda_ranks)
        lda_rels = get_frms(lda_ranks, goldsets)

    lsi_rels = list()
    if project.lsi:
        lsi.save(lsi_fname)
        write_ranks(project, 'temporal_lsi', lsi_ranks)
        lsi_rels = get_frms(lsi_ranks, goldsets)

    return lda_rels, lsi_rels



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

                    goldsets[id_].extend([item for kind, item in changes])

    logger.info("Returning %d goldsets", len(goldsets))
    return goldsets

