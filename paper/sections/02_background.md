# Background & Related Work

In this
section, we will first discuss the developer identification problem and 
then review related works for the two categories.

## Developer identification

Software features are functionalities defined by requirements and are
accessible to developers and users. Software change is continual, because
revised requirements lead to new features, increasing expectations lead to
feature enhancements, achieving intended behavior leads to removal of defective
features (i.e., bugs). Users and developers propose change requests to the
project issue tracker. Change requests are sometimes called issue reports, and
specific kinds of change requests include feature requests, enhancement
requests, and bug reports.

Triaging a change request involves steps completed either by one or more
people. How triage occurs differs from
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


## Location-based approaches

Location-based techniques are a common developer identification technique and
build upon feature location techniques.
Location-based approaches resemble a feature location technique in that they
rely on source code entity information to derive a developer, e.g., which
developer has worked on the related classes in the past?

\todo{FLT blah blah}

We use an FLT to identify a ranked list of source code entities related to a
particular task. Using ownership knowledge about the identified entities, we
can choose an appropriate developer to complete the task. For example, if the
FLT identifies the file `foo.py` as the most related entity, then we would want
to know about the maintainer, or owner, of `foo.py`. There are multiple ways to
determine the ownership of a source code entity [@Bird-etal_2011;
@Kagdi-etal_2012; @Corley-etal_2012; @Hossen-etal_2014].

A simple, example ownership metric is the number of times a developer has
committed changes to a file. That is, if over the software history Johanna
modified `foo.py` 20 times, while Heather only has 5 modifications to `foo.py`,
then we consider Johanna as the owner of `foo.py`. Here, we assign all tasks
related to `foo.py` to Johanna.

<!--
@McDonald-Ackerman_2000 present a heuristic-based recommender system named
Expertise Recommender. The recommender uses heuristics derived in a previous
industrial study [@McDonald-Ackerman_1998] on how developers locate expertise.
The Expertise Recommender considers developers' expertise profile based on who
last changed a module, who is closest to the requester in the organization, and
how connected the requester and expert are by using social network analysis.

@Fritz-etal_2007 investigate whether a programmer's activity indicates
knowledge of code in an empirical study on nineteen professional Java
programmers. They study finds that the frequency and recency of interaction is
an indicator of the expertise a developer has on portions of code. They also
report on interviews with developers, finding other indicators that may improve
expertise models based on source code interaction. The indicators include
authorship, role of source code, and the programmer's task.

@Minto-Murphy_2007 propose an approach implemented in a tool named Emergent
Expertise Locator. The approach uses the matrices to produce requirements
coordination by @Cataldo-etal_2006. The matrices represent file dependency, or
how often pairs of files change together, and file authorship, or how often a
developer changes a file.  They evaluate the tool on the history of three open
source projects: Bugzilla, Eclipse, and Firefox. They compare the results to
the approach by @McDonald-Ackerman_2000, and find higher precision
and recall in their own approach.

@Kagdi-etal_2008 present a tool named xFinder to mine developer contributions
in order to recommend a ranked list of developers for a change. The tool
measures the similarity of vectors consisting of the number of commits to a
file, the number of workdays spent on a file, and the most recent workday on
the file. To find an appropriate developer for a file, they measure similarity
between each developer's vector and the file vector.  @Bird-etal_2011 finds
that measuring ownership in this way correlates low ownership with post-release
defects.

@Rahman-Devanbu_2011 use the provenance features of Git to track the ownership
of individual lines of source code.  They then study the impacts of ownership
and experience on software quality by comparing the ownership and experience
characteristics of "implicated code" (lines of code changed to fix bugs) to
those of "normal code." This paper reports an association between strong
ownership by a single developer and implicated code, and an association between
lack of specialized experience on a particular file and implicated code in that
file. This suggests that the best suited developer for change requests is the
developer with the most ownership (i.e., expertise).

@Ma-etal_2009 evaluate the proposed approach by @Schuler-Zimmermann_2008. The
paper proposes a approach of six heuristics: two based on implementation
expertise and four based on usage expertise. The results show
usage-expertise-based recommendations have an accuracy comparable to
implementation-based recommendations.

@Linares-Vasquez-etal_2012 present an approach that does not require mining the
software history nor a learning from previously completed change requests.
Using the author indicated in source code comments with an LSI-based FLT, they
are able to identify the correct developer. @Hossen-etal_2014 extend this
approach to also include change proneness to adjust the rank of relevant source
code entities before selecting a developer.

@Weissgerber-etal_2007 present three visualization techniques that can help a
triager identify the developer most appropriate for a task.
@Bortis-VanderHoek_2013 present an approach that tags bugs to help developers
explore relevant bugs. @Tamrawi-etal_2011 present an incremental DIT approach
based on fuzzy sets. Like @Bassett-Kraft_2013, @Shokripour-etal_2013 show that
using a term weighting scheme increases the accuracy of an DIT.
-->

## Activity-based Approaches

An activity-based approach uses information gained from a developers
*activity*, e.g., which change requests they have worked on in the past.

<!--
@Mockus-Herbsleb_2002 present Expertise Browser to locate expertise. The
browser uses units of experience called Experience Atoms (EA) extracted from
code changes. The number EAs in a certain domain or file determines the
developer's expertise on that domain or file.

@Cubranic-Murphy_2004 propose a machine learning approach that uses text
categorization on change request descriptions. @Cubranic-Murphy_2004 also
report on heuristics used for classification of change requests.
@Anvik-etal_2006 also use machine learning in an approach for semi-automated
triage by using change request history to learn which requests a developer
changes.

@Anvik-Murphy_2007 conduct an empirical evaluation of two approaches for
recommending: one that uses software repository mining, and one that uses
change request repository mining. The evaluation finds that the software
repository approach has higher precision, but lower recall than the change
request repository approach.

@Canfora-Cerulo_2006a propose an information retrieval-based approach that
indexes the textual description of previously resolved change requests. The
documents represent the developer's descriptions of completed change requests.
@Matter-etal_2009 take a slightly different approach and extract developer
documents from source code history. The history-based document measures how
active a developer is with a set of words in a VSM.

@Linstead-etal_2007a report on the use of Author-Topic modeling
[@Steyvers-etal_2004]. The Author-Topic model augments existing topic modeling
[@Blei-etal_2003] to model the distribution of authors over topics in addition
to topics over documents.  @Linstead-etal_2007a use bug reports to attribute
authorship to developers.  The topics allow for comparison of developers based
on their contributions to a topic.

@Guo-etal_2011 report on a large-scale analysis of bug reassignment in
Microsoft Windows Vista operating system project. The study finds five primary
reasons for reassignment: finding the root cause, expertise identification, low
quality reports, difficulty in determining a proper fix, and workload balance.
These reasons suggest considerations in triage that can potentially improve
assignment. The study also validates previous observations [@Guo-etal_2010]
that reassignment is not always harmful, but can be beneficial in finding the
best developer to complete a request.

@Somasundaram-Murphy_2012 propose an approach combining LDA with a machine
learning algorithm for automated change request categorization. Improving
categorization of change requests shows potential benefits to triaging change
requests by reducing the space of expertise that requires consideration.
Knowing which component a request belongs to provides two benefits: knowing the
component reduces the time-to-fix of a report [@Guo-etal_2011], and only
members of the team associated with the component need consideration for
recommendation.  The paper reports a comparative study on three variations of
categorization approaches and finds LDA improves categorization over other
approaches [@Anvik-etal_2006].

@Jeong-etal_2009 use a Markov chain-based learning algorithm that considers bug
reassignment information. Using their bug reassignment model, they reduce the
possibility of a bug reassignment by ensuring the bug is assigned to the
correct developer the first time. They also show that a bug reassignment
increases the time until completion by about 100 days. @Bhattacharya-etal_2012
further employ this idea using different learning algorithms incrementally
improves triaging bugs the first time.
-->

