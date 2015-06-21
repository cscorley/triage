# Conclusion and Future Work

In this work we present preliminary work in using an activity-based DIT using
changeset topic models. We find that our approach outperforms a location-based
DIT in all cases but one. These results are encouraging to keep investigating
the usefulness of our approach.

Future work includes profiling and contrasting the subject systems to determine
why some systems, such as Pig, perform drastically better or worse depending on
the approach. We also plan to execute a *historical simulation*, as in
@Corley-etal_2015, to determine the usefulness of the approach as it would in a
real environment. Further expansion requires expanding the approach outside of
projects that use JIRA and, more importantly, to projects that are not written
primarily in Java.

Additional future work exists in regard to configuration. Most importantly,
like previous work [@Biggers-etal_2014], it would be wise to further
investigate the effects of the LDA variables, such as $K$, $\alpha$ and $\eta$.
In a changeset it may be desirable to parse further for source code entities
using island grammar parsing [@Moonen_2001].  It may also be desirable to only
use portions of the changeset, such as only using added or removed lines, or
extracting changes between the abstract syntax trees [@Fluri-etal_2007]. 
