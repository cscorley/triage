# Modeling Changeset Topics

\begin{figure*}[t]
\centering
\footnotesize
\begin{lstlisting}[language=diff, basicstyle=\ttfamily]
--- a/tika-parsers/src/main/java/org/apache/tika/parser/mail/MailContentHandler.java
+++ b/tika-parsers/src/main/java/org/apache/tika/parser/mail/MailContentHandler.java
@@ -69,9 +69,9 @@ class MailContentHandler implements ContentHandler {
             BodyContentHandler bch = new BodyContentHandler(handler);
             parser.parse(is, new EmbeddedContentHandler(bch), submd);
         } catch (SAXException e) {
-            e.printStackTrace();
+            throw new RuntimeException(new TikaException("Failed to parse email body content", e));
         } catch (TikaException e) {
-            e.printStackTrace();
+            throw new RuntimeException(new TikaException("Failed to parse email body content", e));
         }
     }
\end{lstlisting}
\caption{Example \texttt{git diff}.
This changeset addresses Tika's Issue \#597.
Black or blue lines denote metadata about the change useful for patching.
In particular, black lines represent context lines (beginning with a single space).
Red lines (beginning with a single~\texttt{-}) denote line removals,
and green lines (beginning with a single~\texttt{+}) denote line additions.}
\label{fig:diff}
\vspace{-10pt}
\end{figure*}

<!--
![Developer identification using changesets\label{fig:changeset-triage}](changeset-triage.pdf)
-->

Our activity-based approach relies on modeling changeset topics
[@Corley-etal_2014], a technique that has shown useful for feature location
[@Corley-etal_2015]. We choose to train the model on changesets, rather than
another source of information, because they also represent what we are
primarily interested in: language used by committers.  While a corpus of a
source code snapshot has documents that represent a program, a changeset corpus
has documents that represent programming.

The activity-based approach requires two types of document extraction: one for
the every changeset in the source code history and a developer profile of the
words each individual developer used in those changesets. The left side of
Figure \ref{fig:changeset-triage} illustrates the dual-document extraction
approach.

The document extraction process for the developer corpus is straightforward.
Following @Matter-etal_2009, each developer has their own document consisting
of an aggregation of changesets they have committed to the source code
repository. That is, a document representing a developer consists of only words
that developer has changed.


The document extractor for the changesets parses each changeset for the
removed, added, and context lines. Figure \ref{fig:diff} shows an example
changeset. From there, each line is tokenized by the text extractor.  The same
preprocessor transformations as before occur in both the snapshot and
changesets.  The snapshot vocabulary is always a subset of the changeset
vocabulary [@Corley-etal_2014].


The right side of Figure \ref{fig:changeset-triage} illustrates the retrieval
process. The key intuition to our methodology is that a topic model such as LDA
can infer *any* document's topic proportions regardless of the documents used
to train the model.  In our approach, the documents seen during training are
changesets and the unseen documents are the developer profiles.

Hence, we train a topic model on the changeset corpus and use the model to
index the developer profiles.  Note that we never construct an index of the
changeset documents used for training.  In our approach, we only use the
changesets to continuously update the topic model and only use the developer
profiles for indexing. Also note that since we do not rely on source code at
any point in this approach, it is completely language-agnostic.
