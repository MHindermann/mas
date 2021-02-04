<!-- 
Markdown Syntax: https://www.markdownguide.org/basic-syntax/
PyCharm and Markdown: https://www.jetbrains.com/help/pycharm/markdown.html 
Convert Markdown to LaTeX or PDF: https://pandoc.org/getting-started.html (PS C:\Users\Max\PycharmProjects\mas\text> 
pandoc .\draft.md -s -o draft.pdf)
-->

Here I write a test so see what is going on with this stuff so that I may better understand how it works.

# Machine indexing of institutional repositories: indexing Edoc with Annif and BARTOC FAST as proof of concept

## Introduction

## Prototype

### Aim

### Edoc data

#### Edoc

#### Data extraction
Even though Edoc is a public server, its database does not have a web-ready API. In addition, since Edoc is a 
production server, its underlying database cannot be used directly on pain of disturbing the provided services. The 
data hence needs to be extracted from Edoc in order to work with it. This could for example be achieved by cloning 
the database of the server and running it on a local machine. However, this route was not available due to the limited 
resources of the responsible co-workers. I thus employed a workaround: Edoc has a built-in advanced search tool where 
the results can be exported. Even though it is not possible to extract all database items by default, only one of 
the many available search fields has to be filled in. The complete database can hence be extracted by only 
filling in the `Date` field and using a sufficiently permissive time period such as 1940 to 2020 since the oldest 
record in the database was published in 1942. On January 21 2021 this query yielded 68345 results. These results 
were then exported as a 326 MB JSON file called `1942-2020.json`. `1942-2020.json` has two drawbacks. First, the 
maximum file size on GitHub is 100 MB. And second, `1942-2020.json` is too big to be handled by standard editors 
requiring special editors such as Oxygen. For these reasons 
`1942-2020.json` was split into smaller files that are easier handled and can be uploaded to GitHub. For this we used 
`_Utility.split_json` ending up with files of size 20 MB or less containing 5000 or fewer entries each. These files are
called `raw_master_x-y.json` (where x and y indicate the entries as given by `1942-2020.json`) and saved under 
`edoc/raw`.

#### Data description and analysis

### Sample data set

#### Selection criteria

#### Construction

### Indexing

#### Annif

### Assessment

#### Targets

#### Analysis

### Discussion

## Refinement

## Implementation strategy

## Conclusion