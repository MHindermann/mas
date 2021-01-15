from __future__ import annotations
from typing import List, Optional, Dict, Union, Tuple
from json import load, dump
from datetime import datetime
from annif_client import AnnifClient

import os.path


DIR = os.path.dirname(__file__)


class _Utility:
    """ A collection of utility functions. """

    @classmethod
    def load_json(cls, file_path: str) -> list:
        """ Load a JSON object from file.

        :param file_path: complete path to file including filename and extension
        """

        with open(file_path, encoding="utf-8") as file:
            loaded = load(file)

            return loaded

    @classmethod
    def save_json(cls, data: Union[List, Dict], file_path: str) -> None:
        """ Save data as JSON file.

        :param data: the data to be saved
        :param file_path: complete path to file including filename and extension
        """

        with open(file_path, "w") as file:
            dump(data, file)

    @classmethod
    def split_json(cls, file_path: str, save_path: str) -> None:
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
    """ A collection of data functions. """

    @classmethod
    def select_from_data(cls, data: List[Dict], *fields: str) -> List[Dict]:
        """ Select items from data based on fields.

        :param data: the input data from edoc
        :param fields: the required fields for an item to be selected
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
    def select_from_file(cls, file_path: str, *fields: str) -> None:
        """ Select items from file according to fields.

        For example: select_from_file(DIR + "/raw/2019.json", "title", "abstract", "keywords", "id_number")

        :param file_path: complete path to file including filename and extension
        :param fields: the required fields for an item to be selected
        """

        data = _Utility.load_json(file_path)
        print(f"{file_path} loaded")
        selected = _Data.select_from_data(data, *fields)
        print(f"Items selected")
        save_file_path = DIR + "/selected/" + str(datetime.now()).split(".")[0].replace(":", "-").replace(" ", "-")
        _Utility.save_json(selected, save_file_path)

    @classmethod
    def inspect(cls, data: List[Dict], *fields: str) -> None:
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
    def extract_keywords(cls, file_path) -> List[str]:
        """ Extract keywords per article from file.

        :param file_path: complete path to file including filename and extension
        """
        data = _Utility.load_json(file_path)
        keywords = []
        for item in data:
            keywords.append(item.get("keywords"))

        return keywords

    @classmethod
    def clean_keywords(cls, keywords_per_article: List[str]) -> List[str]:
        """ Turn a list of edoc keywords per article into a clean list of keywords.

        Note that the keywords per article come as string!

        :param keywords_per_article: the edoc keywords
        """

        clean = []
        for keywords in keywords_per_article:
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
    def clean_keyword(cls, keyword: str) -> List[str]:
        """ Clean an edoc keyword.

        :param keyword: the edoc keyword
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
    def make_histogram(cls, keywords: List[str]) -> List[Dict]:
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


class _Annif:

    """ A collection of Annif indexing function. """

    @classmethod
    def make_index(cls, file_path: str,
                   save_path: str,
                   project_ids: List[str],
                   abstract: bool = False,
                   fulltext: bool = False,
                   limit: int = None,
                   threshold: int = None) -> None:
        """ Index items of file with Annif-client.

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

            # add item to output:
            modified_data.append(modified_item)

        _Utility.save_json(modified_data, save_path)

    @classmethod
    def super_make_index(cls, abstract: bool) -> None:
        """ Index items of file with all Annif-client projects.

        :param abstract: toggle use abstract for indexing
        """

        file_path = DIR + "/indexed/indexed_master.json"
        save_path = f"{DIR}/indexed/indexed_working_{str(datetime.now()).split('.')[0].replace(':', '-').replace(' ', '-')}.json"
        project_ids = ["yso-en", "yso-maui-en", "yso-bonsai-en", "yso-fasttext-en", "wikidata-en"]

        _Annif.make_index(file_path=file_path, save_path=save_path, project_ids=project_ids, abstract=abstract)


"""
Here I describe _Utility and _Data in relation to the files in the edoc folder. 

1. We start by extracting all data from edoc. We do this by conducting an advanced search with the date-field set to
1900-2020. On the results page, we export the results as JSON. We use the data extracted pm 20201210 We have 68345 
entries and the file has a size of about 326 MB (which is why it won't fit on GitHub). We call this file 1900-2020.json.

2. We split 1900-2020.json into smaller files that are easier handled and can be uploaded to GitHub. For this we use 
_Utility.split_json and we end up with files of size 20 MB or less containing 5000 or less entries each. These files are
called raw_master_x-y.json where x and y indicate the entries as given by 1900-2020.json. These files are saved under
eodc/raw

3. We select a subset of the entries downloaded from edoc. We use _Data.select_from_file to do so (for convencience on 
1900-2020.json, but it could also be iteratively employed on the files in edoc/raw). The fields chosen are "title", 
"abstract", "keywords" and "id_number". The rationale for choosing these fields is given elsewhere (in short: we need 
items from which to construct a gold standard). The resulting 4111 items are saved as selected_master.json in 
edoc/selected.

4. We extract the keywords (per entry) from the selected entries with _Data.extract_keywords like so:
keywords = _Data.extract_keywords(DIR + "/selected/selected_master.json")
We the save the resulting list under edoc/keywords as keywords_raw.json like so:
_Utility.save_json(keywords, DIR + "keywords/keywords_raw.json")

5. We clean the extracted keywords with _Data.clean_keywords. How and why this is done is explained elsewhere. This is
done as follows:
keywords_raw = _Utility.load_json(DIR + "/keywords/keywords_raw.json")
keywords_clean = _Data.clean_keywords(keywords_raw)
We the save the resulting list under edoc/keywords as keywords_clean.json like so:
_Utility.save_json(clean, DIR + "keywords/keywords_clean.json")

6. We build a histogram of the cleaned keywords used in the selected data with _Data.make_histogram:
keywords_clean = _Utility.load_json(DIR + "/keywords/keywords_clean.json")
histogram = _Data.make_histogram(keywords)
We the save the resulting histogram under edoc/keywords as keywords_clean_histogram.json like so:
_Utility.save_json(histogram, "/keywords/keywords_clean_histogram.json")

(7. We use OpenRefine to match keywords from the cleaned histogram to Wikidata and other ontologies. This is explained
elsewhere).

8. We index the selected items with _Annif.super_make_index. How this works exactly is explained elsewhere. The 
resulting file is indexed_master.json saved in edoc/index. 

9. 
"""