# Background & Related Work

As noted by @Shokripour-etal_2013, there are broadly two categories of
approaches for developer identification: location-based and activity-based.
In this section, we will discuss background and related works of each.


## Location-based approaches

Location-based techniques are a common developer identification technique and
build upon feature location techniques. Location-based approaches resemble a
FLT in that they rely on source code entity information to derive a developer,
e.g., which developer has worked on the related classes in the past?

For example, we can use an FLT to identify a ranked list of source code
entities related to a particular task. Using ownership knowledge about the
identified entities, we can choose an appropriate developer to complete the
task. For example, if the FLT identifies the file `foo.py` as the most related
entity, then we would want to know about the maintainer, or owner, of `foo.py`.
There are multiple ways to determine the ownership of a source code entity
[@Bird-etal_2011; @Kagdi-etal_2012; @Corley-etal_2012; @Hossen-etal_2014].

@Kagdi-etal_2008 present a tool named xFinder to mine developer contributions
in order to recommend a ranked list of developers for a change.
@Bird-etal_2011 finds that measuring ownership in this way correlates low
ownership with post-release defects.
<!-- -->
@Linares-Vasquez-etal_2012 present an approach that does not require mining the
software history nor a learning from previously completed change requests.
Using the author indicated in source code comments with an LSI-based FLT, they
are able to identify the correct developer. @Hossen-etal_2014 extend this
approach to also include change proneness to adjust the rank of relevant source
code entities before selecting a developer. @Zanjani-etal_2015 use *developer
interactions* with source code entities in an editor, rather than developer
contributions, to boost results of a location-based approach.
<!-- -->
@Ma-etal_2009 propose an approach of six heuristics: two based on implementation
expertise and four based on usage expertise to identify developers.
@Shokripour-etal_2013 use term-weighting to increase the performance of their
location-based technique.


## Activity-based Approaches

An activity-based approach uses information gained from a developers
*activity*, e.g., which change requests they have worked on in the past.
Activity-based approaches use the developer's previous contributions in
aggregate to determine which is best fit to work on a particular task.

@Anvik-etal_2006 use machine learning in an approach for semi-automated triage
by using change request history to learn which requests a developer changes.
<!-- -->
@Anvik-Murphy_2007 conduct an empirical evaluation of two approaches for
recommending: one that uses software repository mining, and one that uses
change request repository mining.
<!-- -->
@Canfora-Cerulo_2006a propose an information retrieval-based approach that
indexes the textual description of previously resolved change requests. The
documents represent the developer's descriptions of completed change requests.
@Matter-etal_2009 take a slightly different approach and extract developer
documents from source code history. The history-based document measures how
active a developer is with a set of words in a VSM.
<!-- -->
@Somasundaram-Murphy_2012 propose an approach combining LDA with a machine
learning algorithm for automated change request categorization.
@Tamrawi-etal_2011 model expertise with fuzzy-sets of terms and developers
based on previously fixed bugs.
<!-- -->
@Jeong-etal_2009 use a Markov chain-based learning algorithm that considers bug
reassignment information and reduce the possibility of a bug reassignment by
ensuring the bug is assigned to the correct developer the first time.
@Bhattacharya-etal_2012 further employ this idea using different learning
algorithms incrementally improves triaging bugs the first time.

