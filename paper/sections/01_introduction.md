# Introduction

Developer identification is a triaging activity in which a team member
identifies a list of developers that are most apt to complete a change request
and assigning one or more of those developers to the task
[@McDonald-Ackerman_1998]. @Begel-etal_2010 show that developers need help
finding expertise within their organization *more than they need help finding
source code elements*.

Software features are functionalities defined by requirements and are
accessible to developers and users. Software change is continual, because
revised requirements lead to new features, increasing expectations lead to
feature enhancements, achieving intended behavior leads to removal of defective
features (i.e., bugs). Users and developers propose change requests to the
project issue tracker. Change requests are sometimes called issue reports, and
specific kinds of change requests include feature requests, enhancement
requests, and bug reports.

Triaging a change request involves steps completed either by a single person or
by a team of developers in a triage meeting. How triage occurs differs from
team to team, but the general steps required are as follows. First, the
triager(s) must see if the request has enough information for consideration.
The triager marks the request as a duplicate if the request already exists
elsewhere in the tracker or was previously completed. After confirming that the
request is new and has enough information, the triager decides whether the
request will be completed, and how soon it will be completed, based on its
severity, frequency, risk, and other factors. Finally, the triager assigns a
request to the developer. Ultimately, the goal of triage is deciding priority
of the request and assignment to the developer that is best suited to complete
the change request.

Triaging is a common and difficult task. Triage is even more difficult on
projects where developer teams are large or geographically distributed
[@Herbsleb-etal_2001]. Triaging requires contextual knowledge about the
product, team structure, individual expertise, workload balance, and
development schedules in order to correctly assign a change request. A project
member triaging a change request will need to consider these factors in order
to correctly assign the change request to a set of developers with appropriate
expertise [@McDonald-Ackerman_1998].

Triaging can be a time consuming and error prone process when done manually.
A triager reassigns a change request assigned in error to a different
developer, or the original developer reassigns the request themselves.
@Jeong-etal_2009 found that reassignment occurs between 37%--44% of the time
and introduces an average of 50 days delay in completing the request. Automated
support for triaging helps to decrease change request time-to-triage and to
correct, or prevent, human error.

@McDonald-Ackerman_1998 show that there are two expertise finding problems:
identification and selection. In a semiautomated system, the system
automatically identifies and suggests an expert for assignment. In a
fully-automated system, the system identifies and assigns a developer to the
change request. @Anvik-etal_2006 notes that a fully-automated approach may not
be feasible given the amount of contextual knowledge required for triage.

