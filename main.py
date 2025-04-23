import getPage as GetPage
import indexer as Indexer
import searchEngine as SearchEngine

from typing import List

if __name__ == "__main__":
    print("======================= Crawler =======================")
    start_url = 'https://www.cse.ust.hk/~kwtleung/COMP4321/testpage.htm'
    num_pages = 2 # change this to 10 in final submission
    spider = GetPage.Spider(start_url, num_pages)
    spider.crawl()

    print("\n\n\n")
    print("======================= Stop Remove & Stem =======================")
    files: List[Indexer.File] = []
    for page in spider.pages:
        file = Indexer.File(page)
        files.append(file)
        print(f"ID: {file.file_id}, Title: {file.title}, Body: {file.body}")

    print("\n\n\n")
    print("======================= Search Engine =======================")
    engine = SearchEngine.SearchEngine()
    for file in files:
        engine.indexDoc(file.file_id, file.title, file.body)
    print("Search for 'hong kong':", engine.search("hong kong"))
    print("Search for phrase '\"science\"':", engine.search('"science"'))
    print("Search for 'universities':", engine.search("universities"))
    print("Search for 'hong kong universities':", engine.search("hong kong universities"))