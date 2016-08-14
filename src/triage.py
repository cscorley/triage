#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import print_function

import logging
logger = logging.getLogger('triage')

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
        ranks, name = common.check_ranks(project, each, 'triage')
        names[each] = name

        if ranks:
            results[each] = get_frms(ranks, goldsets)
        else:
            results[each] = None

    logger.info("NAMES %s", str(names))

    if any([x is None for x in results.values()]):
        repos = load_repos(project)

        # create/load document lists
        queries = create_queries(project)
        ids = load_ids(project)

        ownership = build_ownership(project, repos)

        # get corpora
        changeset_corpus = create_corpus(project, repos, ChangesetCorpus, use_level=False)
        developer_corpus = create_developer_corpus(project, repos, changeset_corpus)
        release_corpus = create_release_corpus(project, repos)

        collect_info(project, repos, queries, goldsets, changeset_corpus, release_corpus)

        if 'release' in project.source and results['release'] is None:
            fn = 'release-%s' % project.level
            # the kagdi approach
            #results['release'] = run_ownership(project, release_corpus, ownership,
            #                                   queries, goldsets, fn, names['release'])

            # the matter approach
            result, train_perplexity, other_perplexity = run_basic(project,
                    release_corpus, developer_corpus, queries, goldsets, fn,
                    names['release'])

            common.append_perplexity(project, train_perplexity, "release-triage-train-perplexity")
            common.append_perplexity(project, other_perplexity, "release-triage-other-perplexity")

            results['release'] = result

        if 'changeset' in project.source and results['changeset'] is None:
            fn = 'changeset-%s' % project.changeset_config_string
            result, train_perplexity, other_perplexity = run_basic(project,
                    changeset_corpus, developer_corpus, queries, goldsets, fn,
                    names['changeset'])

            common.append_perplexity(project, train_perplexity, "changeset-triage-train-perplexity")
            common.append_perplexity(project, other_perplexity, "changeset-triage-other-perplexity")

            results['changeset'] = result

        if 'temporal' in project.source and results['temporal'] is None:
            results['temporal'] = run_temporal(project, repos, changeset_corpus,
                                                create_developer_corpus,
                                                queries, goldsets, names['temporal'])

    return results


def run_ownership(project, corpus, ownership, queries, goldsets, kind, rank_name):
    logger.info("Running ownership-based evaluation on the %s", kind)

    if project.model == "lda":
        model, _ = create_model(project, corpus, corpus.id2word, LdaModel, kind)

    if project.model == "lsi":
        model, _ = create_model(project, corpus, corpus.id2word, LsiModel, kind)

    query_topic = get_topics(model, queries)
    doc_topic = get_topics(model, corpus)

    ranks = get_rank(query_topic, doc_topic)
    owners = rank2owner(ranks, ownership, goldsets)
    write_ranks(project, rank_name, owners)

    return get_frms(owners, goldsets)

def rank2owner(ranks, ownership, goldsets):
    logger.info("Getting owner ranks from %d ranks over %d ownerships", len(ranks), len(ownership))
    owner_ranks = dict()

    for qid, rank in ranks.items():
        if qid not in owner_ranks:
            owner_ranks[qid] = list()

        for idx, distance, d_name in rank:
            if d_name not in ownership:
                logger.debug('Could not find %s in ownership')
                continue

            owners = list(sorted(ownership[d_name].items(), key=lambda x: x[1], reverse=True))
            best_score = 0
            bests = list()
            for owner, score in owners:
                # get the owner, including all ties.
                if best_score and score < best_score:
                    break

                best_score = score
                bests.append((distance, (owner, score)))

            owner_ranks[qid].extend(bests)

        # only allow a dev to be recommended once
        owner_ranks[qid].sort()
        new_ranks = list()
        seen = set()
        for dist, meta in owner_ranks[qid]:
            owner, score = meta
            if owner not in seen:
                new_ranks.append((dist, meta))
                seen.add(owner)
        owner_ranks[qid] = new_ranks


    return_ranks = dict()
    for qid, rank in owner_ranks.items():
        l = list()
        for idx, data in enumerate(rank):
            dist, meta = data
            owner, score = meta
            if owner in goldsets[qid]:
                l.append((idx+1, dist, owner))

        return_ranks[qid] = l

    logger.info("Returning %d owner ranks", len(return_ranks))
    return return_ranks

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

                    # goldsets[id_].extend([item for kind, item in changes])
                    # need to underscore because gensim corpus funtime
                    committer = to_unicode(commit.committer.replace(" ", "_"))
                    goldsets[id_].add(committer)


    logger.info("Returning %d goldsets", len(goldsets))
    return goldsets

def create_developer_corpus(project, repos, changesets, ref=None):
    corpus_fname_base = project.full_path + 'Developer'
    if ref:
        corpus_fname_base += '-' + ref

    corpus_fname = corpus_fname_base + '.mallet.gz'
    dict_fname = corpus_fname_base + '.dict.gz'


    dev_words = dict()
    if not os.path.exists(corpus_fname):
        changesets.metadata = True
        for doc, meta in changesets:
            cid, label = meta

            commit = None
            for repo in repos:
                if cid in repo:
                    commit = repo[str(cid)]
                    break

            if commit:
                if ref and ref == commit.id:
                    break

                dev = to_unicode(commit.committer)
                dev = dev.replace(" ", "_") # mallet cant have spaces in ids
                if dev not in dev_words:
                    dev_words[dev] = list()

                dev_words[dev].extend(doc)


        changesets.metadata = False
        dev_words = [(v, (k, 'dev')) for k, v in dev_words.items()]

        MalletCorpus.serialize(corpus_fname, dev_words, id2word=changesets.id2word,
                            metadata=True)

        changesets.id2word.save(dict_fname)

    id2word = None
    if os.path.exists(dict_fname):
        id2word = Dictionary.load(dict_fname)

    corpus = MalletCorpus(corpus_fname, id2word=id2word)

    return corpus

