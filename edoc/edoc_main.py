from __future__ import annotations
from typing import List, Optional, Dict, Union, Tuple
from json import load, dump
from datetime import datetime
from annif_client import AnnifClient
import os.path
import urllib3
import xmltodict
import ast


DIR = os.path.dirname(__file__)


class _Utility:
    """ A collection of utility functions. """

    @classmethod
    def load_json(cls,
                  file_path: str) -> list:
        """ Load a JSON object from file.

        :param file_path: complete path to file including filename and extension
        """

        with open(file_path, encoding="utf-8") as file:
            loaded = load(file)

            return loaded

    @classmethod
    def save_json(cls,
                  data: Union[List, Dict],
                  file_path: str) -> None:
        """ Save data as JSON file.

        :param data: the data to be saved
        :param file_path: complete path to file including filename and extension
        """

        with open(file_path, "w") as file:
            dump(data, file)

    @classmethod
    def split_json(cls,
                   file_path: str,
                   save_path: str) -> None:
        """ Split a JSON file into files not larger than 100MB.

        :param file_path: complete path to file including filename and extension
        :param save_path: complete path to save folder including filename without extension
        """

        size = int(os.path.getsize(file_path)/(1024*1024))
        print(f"{file_path} is {size} MB")

        if size > 99:
            data = cls.load_json(file_path)
            maximum = len(data)
            position = 0
            while position < maximum:
                json_slice = data[position:position + 5000]
                cls.save_json(json_slice, DIR + f"{save_path}_{position}-{position + 5000}.json")
                position = position + 5000


class _Data:
    """ A collection of edoc data functions. """

    @classmethod
    def select_from_data(cls,
                         data: List[Dict],
                         *fields: str) -> List[Dict]:
        """ Select items from data based on non-empty fields.

        Only items where all required fields are non-empty are sample.

        :param data: the input data
        :param fields: the required fields for an item to be sample
        """

        selected = []
        for item in data:
            keep_item = True
            for field in fields:
                if field not in item:
                    keep_item = False
                    break
            if keep_item is True:
                selected.append(item)

        return selected

    @classmethod
    def select_from_file(cls,
                         file_path: str,
                         *fields: str) -> None:
        """ Select items from file according to fields.

        For example: select_from_file(DIR + "/raw/2019.json", "title", "abstract", "keywords", "id_number")

        :param file_path: complete path to file including filename and extension
        :param fields: the required fields for an item to be sample
        """

        data = _Utility.load_json(file_path)
        print(f"{file_path} loaded")
        selected = _Data.select_from_data(data, *fields)
        print(f"Items sample")
        save_file_path = DIR + "/sample/" + str(datetime.now()).split(".")[0].replace(":", "-").replace(" ", "-")
        _Utility.save_json(selected, save_file_path)

    @classmethod
    def inspect(cls,
                data: List[Dict],
                *fields: str) -> None:
        """ Print fields of items in data.

        :param data: data to be inspected
        :param fields: fields to focus on
        """

        item_nr = 1
        for item in data:
            print(f"Item #{item_nr}")
            for field in fields:
                if field in item:
                    print(f"{str(field)}: {item.get(field)}")
            item_nr = item_nr + 1
            print("**********")

        print(f"Items in data: {len(data)}")

    @classmethod
    def enrich_author_keywords(cls,
                               file_path: str,
                               save_path: str) -> None:
        """ Enrich author keywords.

        For each edoc item: the string of author keywords is cut into single keywords and each keyword is cleaned. Each
        keyword is then enriched with Qid, MeSH and YSO ID if available.

        :param file_path: complete path to file including filename and extension
        :param save_path: complete path to save folder including filename without extension
        """

        data = _Utility.load_json(file_path)
        modified_data = []

        for item in data:

            # make deep copy of item:
            modified_item = dict(item)

            # clean keywords
            keywords = modified_item.get("keywords")
            keywords_clean = _Keywords.clean_keywords([keywords])

            # enrich keywords
            enriched_keywords = []
            for keyword in keywords_clean:
                enriched_keywords.append(cls.map2reference(keyword))

            modified_item["keywords enriched"] = enriched_keywords

            # add modified item to output:
            modified_data.append(modified_item)

        _Utility.save_json(modified_data, save_path + ".json")

    @classmethod
    def map2reference(cls,
                      keyword: str) -> Dict:
        """ Map a keyword to its reference keyword.

        Keyword must first be cleaned by corresponding _Keyword method.

        :param keyword: the keyword
        """

        # load reference keywords (for now keywords_clean_histogram_enriched.csv):
        keywords_reference = _Utility.load_json(DIR + "/keywords/keywords_reference.json")

        # enrich keywords
        for entry in keywords_reference:
            if entry["keyword clean"] == keyword:
                return entry

        print(f"No reference found for {keyword}!")

    @classmethod
    def enrich_with_mesh(cls,
                         file_path: str,
                         save_path: str) -> None:
        """ Enrich edoc data per item with MeSH keywords from PubMed if available.

        :param file_path: complete path to file including filename and extension
        :param save_path: complete path to save folder including filename without extension
        """

        data = _Utility.load_json(file_path)
        modified_data = []

        for item in data:

            # sanity check:
            print(item.get("title"))

            # make deep copy of item:
            modified_item = dict(item)

            # find PubMed ID if available
            identifiers = modified_item.get("id_number") # identifiers is list of dict
            for identifier in identifiers:
                if identifier.get("type") == "pmid":
                    pmid_id = identifier.get("id")

                    # add MeSH based on PubMed ID:
                    mesh = cls.fetch_mesh(pmid_id)
                    modified_item["mesh"] = mesh

            # add modified item to output:
            modified_data.append(modified_item)

        _Utility.save_json(modified_data, save_path + ".json")

    @classmethod
    def fetch_mesh(cls,
                   pubmed_id: str) -> List[Dict]:
        """ Fetch MeSH keywords for article based on PubMed ID.

        :param pubmed_id: article PubMed ID
        """

        mesh = []

        http = urllib3.PoolManager()
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pubmed_id}&retmode=xml"
        response = http.request('GET', url)
        article = xmltodict.parse(response.data)
        try:
            for item in article["PubmedArticleSet"]["PubmedArticle"]["MedlineCitation"]["MeshHeadingList"]["MeshHeading"]:
                mesh.append({"MeSH descriptor ID": item["DescriptorName"]["@UI"], "MeSH label": item["DescriptorName"]["#text"]})
        except (TypeError, KeyError):
            pass

        return mesh

    @classmethod
    def enrich_with_annif(cls,
                          file_path: str,
                          save_path: str,
                          project_ids: List[str],
                          abstract: bool = False,
                          fulltext: bool = False,
                          limit: int = None,
                          threshold: int = None) -> None:
        """ Enrich items from file with automatic keywords using Annif-client.

        Available Annif-client project IDs are yso-en, yso-maui-en, yso-bonsai-en, yso-fasttext-en, wikidata-en.

        :param file_path: complete path to file including filename and extension
        :param save_path: complete path to save folder including filename without extension
        :param project_ids: Annif-client project IDs to be used
        :param abstract: toggle use abstract for indexing, defaults to False
        :param fulltext: toggle use fulltext for indexing, defaults to False
        :param limit: Annif-client limit, defaults to None
        :param threshold: Annif-client threshold, defaults to None
        """

        data = _Utility.load_json(file_path)
        client = AnnifClient()
        modified_data = []

        for item in data:

            # sanity check:
            print(item.get("title"))

            # make deep copy of item:
            modified_item = dict(item)

            # make text to be indexed:
            text = modified_item.get("title")
            if abstract is True:
                text = text + " " + modified_item.get("abstract")
            if fulltext is True:
                pass
                # TODO: add fulltext support

            for project_id in project_ids:

                # make name for indexing:
                name = f"{project_id}-{str(abstract)}-{str(fulltext)}-{str(threshold)}-{str(limit)}"

                # check if item has annif-component:
                if "annif" in modified_item:
                    if name in modified_item.get("annif"):
                        print(f"WARNING: {name} is already available and is currently being overridden!")
                else:
                    modified_item["annif"] = dict()

                # actual indexing via Annif-client:
                results = client.suggest(project_id=project_id, text=text, threshold=threshold, limit=limit)

                # add results to item:
                modified_item["annif"][name] = results

            # add modified item to output:
            modified_data.append(modified_item)

        _Utility.save_json(modified_data, save_path)

    @classmethod
    def super_enrich_with_annif(cls,
                                abstract: bool) -> None:
        """ Enrich items with automatic keywords using all Annif-client projects.

        :param abstract: toggle use abstract for indexing
        """

        file_path = DIR + "/indexed/indexed_master.json"
        save_path = f"{DIR}/indexed/indexed_working_{str(datetime.now()).split('.')[0].replace(':', '-').replace(' ', '-')}.json"
        project_ids = ["yso-en", "yso-maui-en", "yso-bonsai-en", "yso-fasttext-en", "wikidata-en"]

        _Data.enrich_with_annif(file_path=file_path, save_path=save_path, project_ids=project_ids, abstract=abstract)


class _Keywords:
    """ A collection of functions for manipulating edoc author keywords. """

    @classmethod
    def extract_keywords(cls,
                         file_path: str) -> List[str]:
        """ Extract keywords per item from file.

        :param file_path: complete path to file including filename and extension
        """
        data = _Utility.load_json(file_path)
        keywords = []
        for item in data:
            keywords.append(item.get("keywords"))

        return keywords

    @classmethod
    def clean_keywords(cls,
                       keywords_per_item: List[str]) -> List[str]:
        """ Turn a string of keywords per item into a list of cleaned (=normalized) keywords.

        :param keywords_per_item: the keywords
        """

        assert(isinstance(keywords_per_item, list))

        clean = []
        for keywords in keywords_per_item:
            try:
                # generate distinct keywords from string:
                if ";" in keywords:
                    keywords = keywords.split(";")
                elif "–" in keywords:
                    keywords = keywords.split("-")
                else:
                    keywords = keywords.split(",")
                # clean keywords:
                for keyword in keywords:
                    clean = clean + cls.clean_keyword(keyword)
            except TypeError:
                print(f"TypeError with {keywords}")
        return clean

    @classmethod
    def clean_keyword(cls,
                      keyword: str) -> List[str]:
        """ Clean a keyword.

        :param keyword: the keyword
        """

        clean = []
        # make lower case:
        keyword = keyword.lower()
        # remove *:
        keyword = keyword.replace("*", "")
        # remove whitespace:
        keyword = keyword.strip()

        new_keywords = []
        if "," in keyword:
            new_keywords = keyword.split(",")
        elif "/" in keyword:
            new_keywords = keyword.split("/")
        elif ":" in keyword:
            new_keywords = keyword.split(":")
        # untested but required
        # elif "&" in keyword:
        #    new_keywords = keyword.split("&")

        if len(new_keywords) > 0:
            for new_keyword in new_keywords:
                clean = clean + cls.clean_keyword(new_keyword)
            return clean
        else:
            clean.append(keyword)
            return clean

    @classmethod
    def make_histogram(cls,
                       keywords: List[str]) -> List[Dict]:
        """ Make a histogram for keywords.

        :param keywords: the keywords
        """
        histogram = dict()
        for keyword in keywords:
            if keyword in histogram:
                histogram[keyword] = histogram[keyword] + 1
            else:
                histogram[keyword] = 1

        openrefine_histogram = []
        for entry in histogram:
            openrefine_histogram.append({"keyword": entry, "occurrences": histogram.get(entry)})

        return openrefine_histogram

    @classmethod
    def enrich_with_yso(cls,
                        file_path: str,
                        save_path: str):
        """ Blah.

        :param file_path: complete path to file including filename and extension
        :param save_path: complete path to save folder including filename without extension
        """

        data = _Utility.load_json(file_path)
        modified_data = []

        for item in data:
            # make deep copy of item:
            modified_item = dict(item)

            # if YSO ID is missing, fetch it if available; but discard entries without clean keywords:
            if modified_item.get("yso id") == "":
                if modified_item.get("keyword clean") == "":
                    continue
                else:
                    yso = cls.fetch_yso(modified_item.get("keyword clean"))
                    modified_item["yso id"] = yso
                    print(yso)

            modified_data.append(modified_item)

        _Utility.save_json(modified_data, save_path)

    @classmethod
    def fetch_yso(cls,
                  keyword: str) -> Union[str, None]:
        """ Fetch the YSO ID for a keyword if any.

        :param keyword: the keyword
        """

        http = urllib3.PoolManager()
        url = f"https://api.finto.fi/rest/v1/yso/search?query={keyword}&lang=en"
        response = http.request('GET', url)

        try:
            results = ast.literal_eval(response.data.decode("UTF-8")).get("results")
            return results[0].get("localname")[1:]
        except (IndexError, SyntaxError):
            return None


class _Analysis:
    """ A of data images functions. """


#_Keywords.enrich_with_yso(DIR + "/keywords/keywords_reference.json", DIR + "/keywords/keywords_reference_test.json")

#print(_Keywords.fetch_yso("drug"))


# call this after completing the construction of the reference keywords:
# _Data.enrich_author_keywords(DIR + "/indexed/indexed_master_mesh.json", DIR + "/indexed/indexed_master_mesh_enriched")

"""
Here I describe _Utility and _Data in relation to the files in the edoc folder. 

OK 1. We start by extracting all data from edoc. We do this by conducting an advanced search with the date-field set to
1900-2020. On the results page, we export the results as JSON. We use the data extracted pm 20201210 We have 68345 
entries and the file has a size of about 326 MB (which is why it won't fit on GitHub). We call this file 1900-2020.json.

OK 2. We split 1900-2020.json into smaller files that are easier handled and can be uploaded to GitHub. For this we use 
_Utility.split_json and we end up with files of size 20 MB or less containing 5000 or less entries each. These files are
called raw_master_x-y.json where x and y indicate the entries as given by 1900-2020.json. These files are saved under
eodc/raw

3. We select a subset of the entries downloaded from edoc. We use _Data.select_from_file to do so (for convencience on 
1900-2020.json, but it could also be iteratively employed on the files in edoc/raw). The fields chosen are "title", 
"abstract", "keywords" and "id_number". The rationale for choosing these fields is given elsewhere (in short: we need 
items from which to construct a gold standard). The resulting 4111 items are saved as sample_master.json in 
edoc/sample.

4. We extract the keywords (per entry) from the sample entries with _Keywords.extract_keywords like so:
keywords = _Keywords.extract_keywords(DIR + "/sample/sample_master.json")
We the save the resulting list under edoc/keywords as keywords_raw.json like so:
_Utility.save_json(keywords, DIR + "/keywords/keywords_extracted.json")

5. We clean the extracted keywords with _Keywords.clean_keywords. How and why this is done is explained elsewhere. This 
is done as follows:
keywords_extracted = _Utility.load_json(DIR + "/keywords/keywords_extracted.json")
keywords_clean = _Keywords.clean_keywords(keywords_extracted)
We the save the resulting list under edoc/keywords as keywords_clean.json like so:
_Utility.save_json(clean, DIR + "keywords/keywords_clean.json")

6. We build a histogram of the cleaned keywords used in the sample data with _Keyword.make_histogram:
keywords_clean = _Utility.load_json(DIR + "/keywords/keywords_clean.json")
histogram = _Keyword.make_histogram(keywords)
We the save the resulting histogram under edoc/keywords as keywords_clean_histogram.json like so:
_Utility.save_json(histogram, "/keywords/keywords_clean_histogram.json")

7a. We create a list of reference keywords from the author keywords. To do this we use OpenRefine to match keywords from 
keywords_clean_histogram.json to Wikidata and other ontologies. This is explained elsewhere: draft-document OpenRefine 
methods up to 20210121. The resulting file is exported as keywords_clean_histogram_enriched.csv and then transformed to 
keywords_reference.json. Problem with exports here: multiple IDs are lost  (e.g., keyword clean ethnology has two mesh 
ids Q000208 and D005007 but the second is on different line and exported as standing alone...). 

7b. We try to enrich the reference keywords with YSO ids wherever they are missing. Increases YSO coverage from 1759 to
3185. To do this:
_Keywords.enrich_with_yso(DIR + "/keywords/keywords_reference.json", DIR + "/keywords/keywords_reference-test.json")

8. We index the sample items with _Data.super_enrich_with_annif. How this works exactly is explained elsewhere. The 
resulting file is indexed_master.json saved in edoc/index. 

9. We enrich the sample items with MeSH keywords from PubMed if available (item needs a PubMed ID and items needs to
be indexed with MeSH on PubMed, 1653 items match this requirement); the resulting file is indexed_master_mesh.json. Like 
so: 
_Data.enrich_with_mesh(DIR + "/indexed/indexed_master.json", DIR + "/indexed/indexed_master_mesh")

10. We enrich the sample items with cleaned author keywords (including, if available, Qid, MeSH ID, YSO ID) based on 
the reference keywords; the resulting file is indexed_master_mesh_enriched.json. To do so:
_Data.enrich_author_keywords(DIR + "/indexed/indexed_master_mesh.json", DIR + "/indexed/indexed_master_mesh_enriched")
NOTE: rerun this whenever we amend the reference keywords!
"""

#TODO:
"""
A. For each set of keywords and article in sample_master.json, map each keyword to its corresponding keyword in 
keywords_clean_histogram.json. This is required so that we can compute precision and recall. To dos so, we require both 
the concept and its URI.

"""


import scipy.stats as stats

# variable = number of abstracts in different deparments
expected = [5737,
1079,
1523,
16679,
1138,
5091,
11470,
2961,
19560,
2867]

observed = [4463,
658,
918,
2708,
531,
509,
9836,
1807,
15722,
531]

print(stats.chisquare(f_obs=observed, f_exp=expected))

# variable = number of items in a specific department
expected = [5737,
5737,
5737,]
observed = [4463,
363,
4947]

print(stats.chisquare(f_obs=observed, f_exp=expected))

exit()

# see https://medium.com/better-programming/how-to-convert-pdfs-into-searchable-key-words-with-python-85aab86c544f for some ideas

from tika import parser
rawText = parser.from_file(DIR + "/fulltexts/2020_18_Informed by wet feet_How do floods affect property prices.pdf")
rawList = rawText['content'].splitlines()
print(" ".join(rawList))
exit()

#this does not work:
#import PyPDF2
#filename = DIR + "/fulltexts/2020_18_Informed by wet feet_How do floods affect property prices.pdf"
#file = open(filename,'rb')
#pdf_reader = PyPDF2.PdfFileReader(file)

#num_pages = pdf_reader.numPages
#count = 0
#text = ""
#while count < num_pages:
#    page = pdf_reader.getPage(count)
#    count +=1
#    text += page.extractText()

#print(text)

