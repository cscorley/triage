from __future__ import print_function

import csv
import src.main
import src.utils
import logging
import sys
import scipy.stats
import subprocess

projects = src.main.load_projects()

# git_stats is https://github.com/tomgi/git_stats
#   $ gem install git_stats

for project in projects:
    repos = src.main.load_repos(project)
    for c, repo in enumerate(repos):
        output = "git_stats/%s-%s-%d" % (project.name, project.version, c)
        src.utils.mkdir(output)
        cmd = ["git_stats", "generate"]
        cmd.append("--path=" + repo.path)
        cmd.append("--out_path=" +  output)
        cmd.append("--last-commit-sha=" + project.ref)
        cmd.append("--silent")


    print("Running command:\n\t" + " ".join(cmd))
    subprocess.call(cmd)
