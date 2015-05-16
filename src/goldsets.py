#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import print_function

import logging
logger = logging.getLogger('cfl.goldsets')

from StringIO import StringIO
from subprocess import Popen, PIPE
from xml.sax.saxutils import unescape
import codecs
import csv
import errno
import os
import os.path

from gensim.utils import to_unicode
from lxml import etree
import dulwich
import dulwich.diff_tree
import dulwich.patch
import re
import requests
import whatthepatch as wtp

from blocks import Block, File
from corpora import GitCorpus
import main
import utils

def build_developer_goldset(project):
    if os.path.exists(os.path.join(project.full_path, 'DONE')):
        return

    print(project)
    repos = main.load_repos(project)

    # use the gitcorpus cause it'll do all the dulwich setup stuff for us
    # also i am lazy, so...
    corpus = GitCorpus(project=project, repo=repos[0], lazy_dict=True)
    repo = corpus.repo

    goldsets = dict()
    commits = dict()

    for commit, parent, patch, changes, links in walk_changes(project, corpus):
        commits[commit.id] = set(links)

        for gid in links:
            if gid not in goldsets:
                goldsets[gid] = set()

            goldsets[gid].add(commit.committer)

    if len(goldsets) == 0:
        return

    utils.mkdir(os.path.join(project.full_path, 'goldsets', 'committer'))

    with open(os.path.join(project.full_path, 'issue2git.csv'), 'w') as f:
        writer = csv.writer(f)
        for cid, links in commits.items():
            for link in links:
                writer.writerow((link, cid))

    ids = set(goldsets.keys())
    bugs = download_jira_bugs(project, ids)

    with open(os.path.join(project.full_path, 'ids.txt'), 'w') as f:
        for gid in bugs:
            f.write(str(gid) + '\n')

    for gid, goldset in goldsets.items():
        with open(os.path.join(project.full_path, 'goldsets', 'committer',
                                str(gid) + '.txt'), 'w') as f:

            for entity in sorted(list(goldset)):
                f.write(entity + '\n')

    with open(os.path.join(project.full_path, 'DONE'), 'w') as f:
        f.write('yes')

def build_goldset(project):
    if os.path.exists(os.path.join(project.full_path, 'DONE')):
        return

    print(project)
    repos = main.load_repos(project)

    # use the gitcorpus cause it'll do all the dulwich setup stuff for us
    # also i am lazy, so...
    corpus = GitCorpus(project=project, repo=repos[0], lazy_dict=True)
    repo = corpus.repo

    mgoldsets = dict()
    cgoldsets = dict()
    commits = dict()

    for commit, parent, patch, changes, links in walk_changes(project, corpus):
        diffs = wtp.parse_patch(patch)
        commits[commit.id] = set(links)
        for mremoved, madded, cremoved, cadded in parse_diff_changes(project, repo, changes, diffs):

            for gid in links:
                if gid not in mgoldsets:
                    mgoldsets[gid] = set()
                if gid not in cgoldsets:
                    cgoldsets[gid] = set()

                mgoldsets[gid].update(mremoved)
                mgoldsets[gid].update(madded)

                cgoldsets[gid].update(cremoved)
                cgoldsets[gid].update(cadded)

                logger.info("Extracted %d method changes from commit %s for issue %s", len(mgoldsets[gid]), commit.id, gid)
                logger.info("Extracted %d class changes from commit %s for issue %s", len(cgoldsets[gid]), commit.id, gid)

    # cleanup
    for gid, goldset in mgoldsets.items():
        if len(goldset) == 0:
            del mgoldsets[gid]

    for gid, goldset in cgoldsets.items():
        if len(goldset) == 0:
            del cgoldsets[gid]

    if len(mgoldsets) == 0 and len(cgoldsets) == 0:
        return

    utils.mkdir(os.path.join(project.full_path, 'goldsets', 'method'))
    utils.mkdir(os.path.join(project.full_path, 'goldsets', 'class'))

    with open(os.path.join(project.full_path, 'issue2git.csv'), 'w') as f:
        writer = csv.writer(f)
        for cid, links in commits.items():
            for link in links:
                writer.writerow((link, cid))

    ids = set(mgoldsets.keys()) | set(cgoldsets.keys())
    bugs = download_jira_bugs(project, ids)

    with open(os.path.join(project.full_path, 'ids.txt'), 'w') as f:
        for gid in bugs:
            f.write(str(gid) + '\n')

    for gid, goldset in mgoldsets.items():
        with open(os.path.join(project.full_path, 'goldsets', 'method',
                                str(gid) + '.txt'), 'w') as f:

            for entity in sorted(list(goldset)):
                f.write(entity.full_name + '\n')

    for gid, goldset in cgoldsets.items():
        with open(os.path.join(project.full_path, 'goldsets', 'class',
                                str(gid) + '.txt'), 'w') as f:

            for entity in sorted(list(goldset)):
                f.write(entity.full_name + '\n')

    with open(os.path.join(project.full_path, 'DONE'), 'w') as f:
        f.write('yes')

def download_jira_bugs(project, bugs):
    url_base = 'https://issues.apache.org/jira/si/jira.issueviews:issue-xml/%s/%s.xml'
    path = os.path.join(project.full_path, 'queries')
    xmlpath = os.path.join(project.full_path, 'xml')
    utils.mkdir(path)
    utils.mkdir(xmlpath)

    p = etree.XMLParser()
    hp = etree.HTMLParser()

    downloaded = set()

    for bugid in bugs:
        logger.info("Fetching bugid %s", bugid)
        fname = project.name.upper() + '-' + bugid
#        fname = 'HHH-' + bugid
        r = requests.get(url_base % (fname, fname))

        with open(os.path.join(project.full_path, 'xml', str(bugid) + '.xml'),
                  'w') as f:
            f.write(r.text)

        try:
            tree = etree.parse(StringIO(r.text), p)
        except etree.XMLSyntaxError:
            logger.error("Error in XML: %s %s %s", bugid, project, project.version)
            continue
        root = tree.getroot()
        html = root.find('channel').find('item').find('description').text
        summary = root.find('channel').find('item').find('summary').text
        summary = to_unicode(summary)

        htree = etree.parse(StringIO(html), hp)
        desc = ''.join(htree.getroot().itertext())
        desc = to_unicode(desc)

        with codecs.open(os.path.join(path, 'ShortDescription%s.txt' % bugid), 'w', 'utf-8') as f:
            f.write(summary)

        with codecs.open(os.path.join(path, 'LongDescription%s.txt' % bugid), 'w', 'utf-8') as f:
            f.write(desc)

        downloaded.add(bugid)

    return sorted(map(int, list(downloaded)))

def parse_diff_changes(project, repo, changes, diffs):
    for diff in diffs:
        removed = list()
        added = list()
        if not (diff.header.old_path.endswith(".java") or
                diff.header.new_path.endswith(".java")):
            continue

        for r, a, text in diff.changes:
            if r:
                removed.append(r)
            if a:
                added.append(a)

        mremoved_blocks = []
        cremoved_blocks = []
        if diff.header.old_path != "/dev/null":
            logger.info("Generating XML for file %s @ %s", changes.old.path, changes.old.sha)
            ftext = repo[changes.old.sha].as_raw_string()
            mremoved_blocks, cremoved_blocks = get_blocks(ftext, removed)

        madded_blocks = []
        cadded_blocks = []
        if diff.header.new_path != "/dev/null":
            logger.info("Generating XML for file %s @ %s", changes.new.path, changes.new.sha)
            ftext = repo[changes.new.sha].as_raw_string()
            madded_blocks, cadded_blocks = get_blocks(ftext, added)

        yield mremoved_blocks, madded_blocks, cremoved_blocks, cadded_blocks


def walk_changes(project, corpus):
    """ Returns one file change at a time, not the entire diff.

    """
    matcher = re.compile("%s-(\d+)" % project.name, flags=re.IGNORECASE)
    repo = corpus.repo

    for walk_entry in repo.get_walker(include=[corpus.ref_commit_sha]):
        commit = walk_entry.commit
        links = list(matcher.findall(commit.message))

        if links:
            logger.info("Found link in commit %s to issues %s", commit.id, links)
            # initial revision, has no parent
            if len(commit.parents) == 0:
                for changes in dulwich.diff_tree.tree_changes(
                        repo.object_store, None, commit.tree
                ):
                    diff = get_diff(repo, changes)
                    yield commit, None, diff, changes, links

            for parent in commit.parents:
                # do I need to know the parent id?

                for changes in dulwich.diff_tree.tree_changes(
                    repo.object_store, repo[parent].tree, commit.tree
                ):
                    diff = get_diff(repo, changes)
                    yield commit, parent, diff, changes, links

def get_diff(repo, changeset):
    patch_file = StringIO()
    dulwich.patch.write_object_diff(patch_file,
                                    repo.object_store,
                                    changeset.old, changeset.new)
    return patch_file.getvalue()

def get_blocks(text, line_nums):
    cmd = "java -cp ./lib -jar ./lib/srcMLOLOL.jar Java".split()
    xml = pipe(text, cmd)
    xml = xml[len('<?xml version="1.0" encoding="UTF-8" standalone="no"?>'):]

    # while here, we could build the text, too?

    # need huge_tree since the depth gets kinda crazy
    p = etree.XMLParser(huge_tree=True)
    tree = etree.fromstring(xml, parser=p)

    package_name = ''
    pkg = list()
    package = tree.find(".//PackageDeclaration")
    if package is not None:
        qn = package.find(".//QualifiedName")
        for child in qn:
            if child.tag == "CommonToken" and child.attrib["name"] == "Identifier":
                pkg.append(child.text)
        package_name = '.'.join(pkg)

    classTypes = ['ClassDeclaration', 'EnumDeclaration', 'InterfaceDeclaration', 'AnnotationTypeDeclaration']

    # these are the method-like decls that come from the 4 'types' in the grammar
    methodTypes = ["MethodDeclaration", "GenericMethodDeclaration",
                   "ConstructorDeclaration", "GenericConstructorDeclaration",
                   "InterfaceMethodDeclaration", "InterfaceGenericMethodDeclaration",
                   "AnnotationMethodRest"]

    mblocks = list()
    cblocks = list()

    for level in ['class', 'method']:
        if level == 'class':
            findtype = classTypes
        elif level == 'method':
            findtype = methodTypes

        for t in findtype:
            for elem in tree.iterfind(".//" + t):
                # in all types, there is a keyword marking the type
                # with the identifier following immediately
                params = list()
                elem_name = None
                for child in elem:
                    if elem_name is None and child.tag == "CommonToken" and child.attrib["name"] == "Identifier":
                        elem_name = child.text

                    if child.tag == "FormalParameters":
                        for param in child.findall(".//Type"):
                            params.append(''.join(ct.text for ct in param.findall(".//CommonToken")))

                if elem_name is None:
                    elem_name = "$" + t + "$"

                start_line = int(elem.attrib["start_line"])
                end_line = int(elem.attrib["end_line"])

                # TODO, find the body, get actual start_line
                body_line = start_line

                supers = list()
                parent = elem.getparent()
                while parent != None:
                    if parent.tag == 'classCreatorRest':
                        # anonymous class time!
                        supers.append("$classCreatorRest$")
                    else:
                        for child in parent:
                            if child.tag == "CommonToken" and child.attrib["name"] == "Identifier":
                                supers.append(child.text)
                                break
                    parent = parent.getparent()

                if package_name:
                    supers.append(package_name)

                if level == 'method':
                    elem_name += '(' + ','.join(params) + ')'

                elem_name = unescape(elem_name)
                supers = [unescape(s) for s in supers]

                block = Block(t, elem_name, start_line, body_line, end_line,
                            super_block_name=u'.'.join(reversed(supers)))

                if level == 'method':
                    mblocks.append(block)
                elif level == 'class':
                    cblocks.append(block)


    # figure out which methods changed
    mchanged = list()
    for method in mblocks:
        keep = False
        for line_num in line_nums:
            if line_num in method.line_range:
                keep = True
        if keep:
            mchanged.append(method)

    cchanged = list()
    for class_ in cblocks:
        keep = False
        for line_num in line_nums:
            if line_num in class_.line_range:
                keep = True
        if keep:
            cchanged.append(class_)

    # for c in changed:
    #    print(c.full_name)

    # shits the bed on unicode, but above works lol
    # print(changed)

    return mchanged, cchanged


def pipe(text, cmd):
    p = Popen(cmd, stdin=PIPE, stdout=PIPE)
    try:
        p.stdin.write(text)
    except IOError as e:
        if e.errno == errno.EPIPE or e.errno == errno.EINVAL:
            # Stop loop on "Invalid pipe" or "Invalid argument".
            # No sense in continuing with broken pipe.
            pass
        else:
            # Raise any other error.
            raise

    p.stdin.close()
    return p.stdout.read().decode('UTF-8')
