import csv
import gzip
import re
from collections import defaultdict, namedtuple


Developer = namedtuple('Developer', 'name email')


def get_committer(line):
    line = line.partition('> ')[0] + '>'
    parts = line.partition(' <')
    return Developer(parts[0], re.match('([a-zA-Z0-9_@\-\.]+)(?:\s|>)', parts[2]).group(1))


Commit = namedtuple('Commit', 'sha committer')


def get_raw_commits(filename):
    with gzip.open(filename, mode='rt') as logfile:
        sha = None
        while True:
            line = next(logfile).rstrip().partition(' ')
            if sha is None and line and line[0] == 'commit':
                sha = line[2]
            if sha:
                while True:
                    line = next(logfile).rstrip().partition(' ')
                    if line and line[0] == 'committer':
                        yield Commit(sha, get_committer(line[2]))
                        sha = None
                        break


def get_developers(raw_commits):
    """Returns a dict that maps a committer to a canonical developer."""
    developers = dict()
    for commit in raw_commits:
        committer = commit.committer
        if committer not in developers:
            is_new_developer = True
            for developer in developers:
                if committer.name == developer.name or committer.email == developer.email:
                    developers[committer] = developer
                    is_new_developer = False
                    break
            if is_new_developer:
                developers[committer] = committer
    return developers


def get_commits(raw_commits, developers):
    commits = list()
    commit_shas = set() # Some commits are duplicated in changes-file.log.gz
    for raw_commit in raw_commits:
        sha = raw_commit.sha
        if sha not in commit_shas:
            commit_shas.add(sha)
            commits.append(Commit(sha, developers[raw_commit.committer]))
    return commits


def get_shas(filename):
    """Reads a 'changes-file-*.csv' and returns a set of sha strings."""
    shas = set()
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            shas.add(row[0])
    return shas


def main(args):
    if len(args) < 3:
        print('Usage: {0} changes-file.log.gz changes-file-goldset.csv'.format(args[0]))
        return 1

    raw_commits = list(get_raw_commits(args[1]))
    #print('|raw_commits| =', len(raw_commits))

    developers = get_developers(raw_commits)
    print('|developers| =', len(set(developers.values())))

    commits = get_commits(raw_commits, developers)
    print('|commits| =', len(commits))

    goldset = get_shas(args[2])
    print('|goldset| =', len(goldset))

    developer2sha = defaultdict(set)
    developer2goldset = defaultdict(set)
    for commit in commits:
        sha = commit.sha
        developer = developers[commit.committer]
        developer2sha[developer].add(sha)
        if sha in goldset:
            developer2goldset[developer].add(sha)
    print('|developer2sha| =', len(developer2sha))
    print('|developer2goldset| =', len(developer2goldset))


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))

