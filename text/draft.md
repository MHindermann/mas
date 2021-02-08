<!-- 
Markdown Syntax: https://www.markdownguide.org/basic-syntax/
PyCharm and Markdown: https://www.jetbrains.com/help/pycharm/markdown.html 
Convert Markdown to LaTeX or PDF: https://pandoc.org/getting-started.html (PS C:\Users\Max\PycharmProjects\mas\text> 
pandoc .\draft.md -s -o draft.pdf)
-->

Machine indexing of institutional repositories: indexing Edoc with Annif and BARTOC FAST as proof of concept

# Introduction

## Outline

## Method

!! Say something to the effect that all data and code are available on GitHub.

# Prototype

In this chapter, the prototype for a machine indexing of Edoc is presented. The focus is primarily on practical 
implementation although care is taken to spell out design decisions in as much detail as is needed.

## Aim

Let us start by stating the aim of the prototype.  From a functional 
perspective, the prototype takes a subset of the data from Edoc as input and provides index terms for each item in this 
subset as output. In order to fulfill this aim we can distinguish a number of steps that need to be taken:

1. Understand the Edoc data.  
2. Select and construct a sample data set.
3. Index the items in the sample data set.
4. Assess the quality of the output.

In the sections below, these steps will be discussed in detail.

## Edoc data

### Edoc

Edoc is the institutional repository of the University of Basel. It was conceived in 2009 as repository for 
electronic dissertations and grew in scope when the University of Basel adapted its first open access policy in 2013.
As per today Edoc contains roughly 68’000 items. 

Edoc runs on the EPrints 3 document management system [https://github.com/eprints/eprints]. 
!! Perhaps add description of how files are added to Edoc, see PDF in `/todo`.

### Data extraction

Even though Edoc is a public server, its database does not have a web-ready API. In addition, since Edoc is a production
server, its underlying database cannot be used directly on pain of disturbing the provided services. The data hence
needs to be extracted from Edoc in order to work with it. This could for example be achieved by cloning the database of
the server and running it on a local machine. However, this route was not available due to the limited resources of the
responsible co-workers. I thus employed a workaround: Edoc has a built-in advanced search tool where the results can be
exported. Even though it is not possible to extract all database items by default, only one of the many available search
fields has to be filled in. The complete database can hence be extracted by only filling in the `Date` field and using a
sufficiently permissive time period such as 1940 to 2020 since the oldest record in the database was published in 1942.
On January 21 2021 this query yielded 68'345 results. These results were then exported as a 326 MB JSON file
called `1942-2020.json`. `1942-2020.json` has two drawbacks. First, the maximum file size on GitHub is 100 MB. And
second, `1942-2020.json` is too big to be handled by standard editors requiring special editors such as Oxygen. For
these reasons `1942-2020.json` was split into smaller files that are easier handled and can be uploaded to GitHub. For
this
`_Utility.split_json` was used yielding 14 files of size 20 MB or less containing 5000 or fewer entries each. These
files are called `raw_master_x-y.json` (where x and y indicate the entries as given by `1942-2020.json`) and saved under
`/edoc/raw`.

### Data description and analysis

!! Text.

## Sample data set

In this section, I will explain how the sample data set is selected and constructed. By "selection" I mean the task of 
specifiying a subset of the Edoc data and by "construction" I mean the task of implementing this selection. 

### Selection

There are a number of constraints for selecting the sample data set. The first constraint stems from Annif, the 
machine 
indexing framework that will be used. Put simply, machine indexing assigns index terms to a text based on training 
data. The training data consists of a set of texts, a vocabulary, and function from vocabulary to texts. In this 
context we mean by "text" a sequence of words in a natural language and by "vocabulary" a set of words. Intuitively, the training data 
consists of pairs of text and subject terms that meet some standard. The training data and the vocabulary are 
already supplied by Annif, we only need to provide a text for each item that we want to be assigned index terms. 
Therefore, we only select items with text. 


Therefore, only items with texts 






In the case of the Data extracted 
from Edoc, we have three relevant data fields per item: title, abstract and full text. 

(Correspondence theory of indexing: subject term T fits text X iff text X is about T)

### Construction

The first constraint is that each item in the sample data set needs to have a text. Intuitively, this text could 
consist of a title, an abstract, or even a full text, or any combination of the above. Similar to manual indexing, having 
more 
information (that is, longer texts) usually implies a higher indexing quality in machine indexing. However, this 
assumption needs to be confirmed empirically for the given machine indexing framework and data set. If indeed 
confirmed, it might be advisable only to index items that have a certain minimal text length. Therefore, in order to 
construct the sample data set, we require each item to have a non-empty value in the data fields `title`, `abstract`,
and `id_number` as proxy to retrieve a full text remotely. 








comparing the quality and or quantity of output terms 
with some standard(s) – but more on this below [see X].For convenience, let us call this subset simply the sample data. The construction of the sample data is important to facilitate development. The sample data need to be small enough to handle yet not be trivial. They hence should contain the quirks of the complete dataset but on a smaller scale. In other words, we are looking for an abstraction rather than an idealization [QUELLE]. 

### Selection criteria

### Construction

## Indexing

### Annif

## Assessment

### Targets

### Analysis

## Discussion

# Refinement

# Implementation strategy

# Conclusion

# Bibliography

# Appendix

