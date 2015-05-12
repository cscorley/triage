#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import print_function

import logging
logger = logging.getLogger('cfl.goldsets')

import csv
from subprocess import Popen, PIPE
import errno
from StringIO import StringIO
import os
import os.path
from xml.sax.saxutils import unescape

import whatthepatch as wtp
import dulwich
import dulwich.diff_tree
import dulwich.patch
import re
from lxml import etree
from gensim.utils import to_unicode

import main
import utils
from corpora import ChangesetCorpus
from blocks import Block, File

def build_goldset(project):
    print(project)
    repos = main.load_repos(project)
    corpus = ChangesetCorpus(project=project,
                             repo=repos[0],
                             ref='HEAD',  # build ALL the goldsets
                             lazy_dict=True)
    repo = corpus.repo

    if os.path.exists(os.path.join(project.full_path, 'DONE')):
        return

    mgoldsets = dict()
    cgoldsets = dict()
    commits = dict()

    for commit, parent, patch, changes, links in walk_changes(project, repo):
        diffs = wtp.parse_patch(patch)
        for mremoved, madded, cremoved, cadded in parse_diff_changes(project, repo, changes, diffs):
            commits[commit.id] = set(links)

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

    if len(mgoldsets) == 0 and len(cgoldsets) == 0:
        return

    utils.mkdir(os.path.join(project.full_path, 'goldsets', 'method'))
    utils.mkdir(os.path.join(project.full_path, 'goldsets', 'class'))

    ids = set()
    with open(os.path.join(project.full_path, 'issue2git.csv'), 'w') as f:
        writer = csv.writer(f)
        for cid, links in commits.items():
            for link in links:
                writer.writerow((link, cid))
                ids.add(link)

    with open(os.path.join(project.full_path, 'ids.txt'), 'w') as f:
        for gid in sorted(map(int, list(ids))):
            f.write(str(gid) + '\n')

    for gid, goldset in mgoldsets.items():
        with open(os.path.join(project.full_path, 'goldsets', 'method',
                                str(gid) + '.txt'), 'w') as f:

            for entity in sorted(goldset):
                f.write(entity.full_name + '\n')

    for gid, goldset in cgoldsets.items():
        with open(os.path.join(project.full_path, 'goldsets', 'class',
                                str(gid) + '.txt'), 'w') as f:

            for entity in sorted(goldset):
                f.write(entity.full_name + '\n')

    with open(os.path.join(project.full_path, 'DONE'), 'w') as f:
        f.write('yes')

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
            mremoved_blocks, cremoved_blocks = get_blocks(project, repo, changes.old, removed)

        madded_blocks = []
        cadded_blocks = []
        if diff.header.new_path != "/dev/null":
            madded_blocks, cadded_blocks = get_blocks(project, repo, changes.new, added)

        yield mremoved_blocks, madded_blocks, cremoved_blocks, cadded_blocks


def walk_changes(project, repo):
    """ Returns one file change at a time, not the entire diff.

    """
    matcher = re.compile("%s-(\d+)" % project.name, flags=re.IGNORECASE)

    for walk_entry in repo.get_walker():
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

def get_blocks(project, repo, gittree, line_nums):
    cmd = "java -cp ./lib -jar ./lib/srcMLOLOL.jar Java".split()
    logger.info("Generating XML for file %s @ %s", gittree.path, gittree.sha)
    ftext = repo[gittree.sha].as_raw_string()
    xml = pipe(ftext, cmd)
    xml = xml[len('<?xml version="1.0" encoding="UTF-8" standalone="no"?>'):]

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

    types = ['ClassDeclaration', 'EnumDeclaration', 'InterfaceDeclaration'
             'AnnotationTypeDeclaration']

    # these are the method-like decls that come from the 4 'types' in the grammar
    methodTypes = ["MethodDeclaration", "GenericMethodDeclaration",
                   "ConstructorDeclaration", "GenericConstructorDeclaration",
                   "InterfaceMethodDeclaration", "InterfaceGenericMethodDeclaration",
                   "AnnotationMethodRest"]

    mblocks = list()
    cblocks = list()

    if project.level == 'class':
        findtype = types
    elif project.level == 'method':
        findtype = methodTypes

    for level in ['class', 'method']:
        if level == 'class':
            findtype = types
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
