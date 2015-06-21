# Introduction

Developer identification is a triaging activity in which a team member
identifies a list of developers that are most apt to complete a task and
assigning one or more of those developers to the task
[@McDonald-Ackerman_1998]. @Begel-etal_2010 show that developers need help
finding expertise within their organization *more than they need help finding
source code elements*.

Triaging is a common and difficult task. Triage is even more difficult on
projects where developer teams are large or geographically distributed
[@Herbsleb-etal_2001]. Triaging requires contextual knowledge about the
product, team structure, individual expertise, workload balance, and
development schedules in order to correctly assign a change request. A project
member triaging a change request will need to consider many factors in order
to correctly assign the change request to a set of developers with appropriate
expertise [@McDonald-Ackerman_1998].

Triaging can be a time consuming and error prone process when done manually.
A triager can reassign a change request assigned in error to a different
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

Recent advancements in automating triage often involve a range of heterogeneous
information mined from many sources [@Kagdi-etal_2012;
@Linares-Vasquez-etal_2012; @Hossen-etal_2014; @Zanjani-etal_2015]. The need
for heterogeneous sources is intuitive given that manual triage also requires
consideration of several factors. However, many of these approaches are
location-based, and as such must rely on a feature location technique (FLT) to
locate relevant source code entities before identifying a developer with the
mined information. Hence, their accuracy is heavily influenced by the accuracy
of the underlying FLT to locate the correct source code entities.

In this paper, we propose an activity-based developer identification technique
(DIT) that uses changeset topic modeling to determine appropriate developers by
the words they have changed. The preliminary evaluation compares the approach
to a location-based technique, both using latent Dirichlet allocation (LDA)
[@Blei-etal_2003] as a topic modeler. Our benchmark consists of over 1300
issues from 7 Apache open source Java systems. Our results shows improvements
when using an activity-based approach for developer identification. Finally, we
conclude and give direction for future work.
