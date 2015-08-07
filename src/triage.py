#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import print_function

import logging
logger = logging.getLogger('triage')

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
    developer_corpus = create_developer_corpus(project, repos, changeset_corpus)
    release_corpus = create_release_corpus(project, repos)

    collect_info(project, repos, queries, goldsets, changeset_corpus, release_corpus)

    ownership_results = run_ownership(project, release_corpus,
                                      ownership, queries, goldsets,
                                      'Release', 'Triage')

    changeset_results = run_basic(project, changeset_corpus,
                                  developer_corpus, queries, goldsets,
                                  'Changeset', 'Triage')

    results = dict()

    if project.temporal:
        try:
            temporal_lda, temporal_lsi = run_temporal(project, repos,
                                                    changeset_corpus, queries,
                                                    goldsets)
        except IOError:
            logger.info("Files needed for temporal evaluation not found. Skipping.")
        else:
            if project.model == "lda":
                results['temporal_lda'] = do_science(temporal_lda, changeset_lda, ignore=True)
            if project.model == "lsi":
                results['temporal_lsi'] = do_science(temporal_lsi, changeset_lsi, ignore=True)

    # do this last so that the results are printed together
    if project.model == "lda":
        results['basic_lda'] = do_science(changeset_results['lda'], ownership_results['lda'])

    if project.model == "lsi":
        results['basic_lsi'] = do_science(changeset_results['lsi'], ownership_results['lsi'])

    return results


def run_ownership(project, corpus, ownership, queries, goldsets, kind, experiment, use_level=False):
    logger.info("Running ownership-based evaluation on the %s", kind)
    results = dict()
    if project.model == "lda":
        rank_name = '-'.join([kind, experiment, 'lda', project.lda_config_string]).lower()
        try:
            lda_owners = read_ranks(project, rank_name)
            logger.info("Sucessfully read previously written %s LDA ranks", kind)
            exists = True
        except IOError:
            exists = False

        if project.force or not exists:
            lda_model, _ = create_lda_model(project, corpus, corpus.id2word, kind, use_level=use_level)
            lda_query_topic = get_topics(lda_model, queries)
            lda_doc_topic = get_topics(lda_model, corpus)

            lda_ranks = get_rank(lda_query_topic, lda_doc_topic)
            lda_owners = rank2owner(lda_ranks, ownership)
            write_ranks(project, rank_name, lda_owners)

        results['lda'] = get_frms(lda_owners, goldsets)

    if project.model == "lsi":
        rank_name = '-'.join([kind, experiment, 'lsi', project.lda_config_string]).lower()
        try:
            lsi_owners = read_ranks(project, rank_name)
            logger.info("Sucessfully read previously written %s LSI ranks", kind)
            exists = True
        except IOError:
            exists = False

        if project.force or not exists:
            lsi_model, _ = create_lsi_model(project, corpus, corpus.id2word, kind, use_level=use_level)
            lsi_query_topic = get_topics(lsi_model, queries)
            lsi_doc_topic = get_topics(lsi_model, other_corpus)

            lsi_ranks = get_rank(lsi_query_topic, lsi_doc_topic)
            lsi_owners = rank2owner(lsi_ranks, ownership)
            write_ranks(project, rank_name, lsi_owners)

        results['lsi'] = get_frms(lsi_owners, goldsets)

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
        lda, lda_fname = create_lda_model(project, None, corpus.id2word,
                                          'Temporal', use_level=False, force=True)

    if project.model == "lsi":
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

        if project.model == "lda":
            lda.update(docs,
                    #chunksize=project.chunksize,
                    offset=project.offset,
                    decay=project.decay)
        if project.model == "lsi":
            lsi.add_documents(docs)

        for qid in git2issue[sha]:
            logger.info('Getting ranks for query id %s', qid)
            # build a developer corpus of items *at this commit*
            developer_corpus = create_developer_corpus(project, repos, corpus, until_ref=sha)

            # do LDA magic
            if project.model == "lda":
                lda_query_topic = get_topics(lda, queries, by_ids=[qid])
                lda_doc_topic = get_topics(lda, developer_corpus)
                lda_subranks = get_rank(goldsets, lda_query_topic, lda_doc_topic)
                if qid in lda_subranks:
                    if qid not in lda_ranks:
                        lda_ranks[qid] = list()

                    rank = lda_subranks[qid]
                    lda_ranks[qid].extend(rank)
                else:
                    logger.info('Couldnt find qid %s', qid)

            # do LSI magic
            if project.model == "lsi":
                lsi_query_topic = get_topics(lsi, queries, by_ids=[qid])
                lsi_doc_topic = get_topics(lsi, developer_corpus)
                lsi_subranks = get_rank(goldsets, lsi_query_topic, lsi_doc_topic)
                if qid in lsi_subranks:
                    if qid not in lsi_ranks:
                        lsi_ranks[qid] = list()

                    rank = lsi_subranks[qid]
                    lsi_ranks[qid].extend(rank)
                else:
                    logger.info('Couldnt find qid %s', qid)

    lda_rels = list()
    if project.model == "lda":
        lda.save(lda_fname)
        write_ranks(project, 'temporal', lda_ranks)
        lda_rels = get_frms(lda_ranks, goldsets)

    lsi_rels = list()
    if project.model == "lsi":
        lsi.save(lsi_fname)
        write_ranks(project, 'temporal_lsi', lsi_ranks)
        lsi_rels = get_frms(lsi_ranks, goldsets)

    return lda_rels, lsi_rels


def rank2owner(ranks, ownership):
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

def create_developer_corpus(project, repos, changesets, until_ref=None):
    corpus_fname_base = project.full_path + 'Developer'
    if until_ref:
        corpus_fname_base += '-' + until_ref

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
                if until_ref and until_ref == commit.id:
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
