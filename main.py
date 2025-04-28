import getPage as GetPage
import indexer as Indexer
import searchEngine as SearchEngine
import database as Database
import argparse

from typing import List

def main(load_from_db: bool = False):
    # Initialize database
    db = Database.Database()
    
    if load_from_db:
        print("======================= Loading Database =======================")
        # Load indexer data from database
        docs, lenDoc, docNo, freqWordDoc = db.load_indexer_data()
        invInd = db.load_inverted_index()

        print(docs)
        print(lenDoc)
        print(docNo)
        print(freqWordDoc)
        print(invInd)
        
        # Create indexer with loaded data
        indexer = Indexer.Indexer()
        indexer.docs = docs
        indexer.lenDoc = lenDoc
        indexer.docNo = docNo
        indexer.freqWordDoc = freqWordDoc
        indexer.invInd = invInd
        
    else:
        print("======================= Crawler =======================")
        start_url = 'https://www.cse.ust.hk/~kwtleung/COMP4321/testpage.htm'
        num_pages = 10
        spider = GetPage.Spider(start_url, num_pages)
        spider.crawl()
        
        # Save crawled pages to database
        db.save_pages(spider.pages)

        print("\n\n\n")
        print("======================= Stop Remove, Stem & Indexer =======================")
        files: List[Indexer.File] = []
        for page in spider.pages:
            file = Indexer.File(page)
            files.append(file)
            print(f"ID: {file.file_id}, Title: {file.title}, Body: {file.body}")
        indexer = Indexer.Indexer()
        for file in files:
            indexer.indexDoc(file.file_id, file.title, file.body)

        # Save indexer data to database
        db.save_indexer_data(indexer.docs, indexer.lenDoc, indexer.docNo, indexer.freqWordDoc)
        db.save_inverted_index(indexer.invInd)
    print("\n\n\n")
    print("======================= Search Engine =======================")
    engine = SearchEngine.SearchEngine(indexer)
    
    # Perform searches and save results
    queries = ["hong kong", '"science"', "universities", "hong kong universities"]
    for query in queries:
        results = engine.search(query)
        # Convert results to list of (doc_id, score) tuples
        result_tuples = [(doc_id, score) for (doc_id, score, wordFreq) in results]
        db.save_search_results(query, result_tuples)
        print(f"Search for '{query}':", result_tuples)
    
    # Close database connection
    db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Search Engine')
    parser.add_argument('--load-db', action='store_true', help='Load indexer data from database instead of crawling')
    args = parser.parse_args()
    
    main(load_from_db=args.load_db)
