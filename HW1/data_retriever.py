from dataclasses import dataclass, asdict
import json
import os
import pickle
import time
from typing import Iterator, List, Set
import requests
from tqdm import tqdm
from multiprocessing import cpu_count
from concurrent.futures import ThreadPoolExecutor, as_completed

import wikipedia
import pandas as pd


wikipedia.set_lang('fa')
wikipedia.set_rate_limiting(True)


@dataclass
class Document:
    title: str
    categories: List[str]
    text: str


def filecache(title: str):
    def decorator(func):
        def wrapper(self: 'DataRetriever', *args, **kwargs):
            cache_path = f'.cache/{title.replace(" ", "_")}_{self.page_per_query}.pkl'
            if os.path.exists(cache_path):
                with open(cache_path, 'rb') as f:
                    print(f'Loading {title} from cache...')
                    return pickle.load(f)
            else:
                result = func(self, *args, **kwargs)
                os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                with open(cache_path, 'wb') as f:
                    pickle.dump(result, f)
                return result
        return wrapper
    return decorator


class DataRetriever:

    def __init__(self, quantities_path: str = 'quantities.csv', page_per_query: int = 10, workers: int = cpu_count()) -> None:
        self.page_per_query = page_per_query
        self.__q = pd.read_csv(quantities_path)
        self.__workers = workers

    @staticmethod
    def __retry(func, *args, **kwargs):
        while True:
            try:
                return func(*args, **kwargs)
            except (requests.exceptions.ConnectionError, wikipedia.exceptions.DisambiguationError):
                time.sleep(1)

    @filecache('page names')
    def get_page_names(self) -> Set[str]:
        result = set()
        with ThreadPoolExecutor(max_workers=self.__workers) as executor:
            futures = [executor.submit(self.search_quantity, q) for q in self.__q['name']]
            for future in tqdm(as_completed(futures), total=len(futures), desc='Getting page names...'):
                result.update(future.result())
        return result

    def search_quantity(self, quantity: str) -> List[str]:
        return self.__retry(wikipedia.search, quantity, results=self.page_per_query)

    @filecache('pages')
    def get_pages(self, names: Set[str]) -> List[wikipedia.WikipediaPage]:
        result = []
        with ThreadPoolExecutor(max_workers=self.__workers) as executor:
            futures = [executor.submit(self.__retry, wikipedia.page, name) for name in list(names)]
            for future in tqdm(as_completed(futures), total=len(futures), desc='Getting pages...'):
                result.append(future.result())
        return result

    @staticmethod
    def get_document(page: wikipedia.WikipediaPage) -> Document:
        return Document(page.title, page.categories, page.content)

    def retrieve(self) -> Iterator[Document]:
        queries = self.get_page_names()
        pages = self.get_pages(queries)
        with ThreadPoolExecutor(max_workers=self.__workers) as executor:
            futures = [executor.submit(self.__retry, self.get_document, page) for page in pages]
            for future in tqdm(as_completed(futures), total=len(futures), desc='Retrieving documents...'):
                yield future.result()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Retrieve data from wikipedia.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--quantities', '-q', type=str, default='quantities.csv',
                        help='Path to the file containing the quantities.')
    parser.add_argument('--page-per-query', '-p', type=int, default=10,
                        help='Number of pages to retrieve per query.')
    parser.add_argument('--workers', '-w', type=int, default=cpu_count(),
                        help='Number of workers to use.')
    parser.add_argument('--output', '-o', type=str, default='data.json',
                        help='Output file name (JSON format)')

    args = parser.parse_args()

    retriever = DataRetriever(args.quantities, args.page_per_query, args.workers)
    documents = retriever.retrieve()
    with open(args.output, 'w') as f:
        json.dump([asdict(doc) for doc in documents], f, indent=2, ensure_ascii=False)
