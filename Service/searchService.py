# Service/searchService.py

import getPage as GetPage
import indexer as Indexer
import database as Database
import searchEngine as SearchEngine


class Page:
    def __init__(self, page_id, parent_id, url, title, last_modified, body):
        self.page_id = page_id
        self.parent_id = parent_id
        self.url = url
        self.title = title
        self.last_modified = last_modified
        self.body = body
        self.child_ids = []


class SearchRes:
    def __init__(self, page_id, parent_id, url, title, last_modified, score):
        self.page_id = page_id
        self.parent_id = parent_id
        self.url = url
        self.title = title
        self.last_modified = last_modified
        self.child_ids = []  # 存储子页面的ID
        self.score = score


class SearchService:
    def __init__(self, load_from_db: bool = False):
        self.db = Database.Database()
        self.indexer = Indexer.Indexer([])

        if load_from_db:
            print("======================= Loading Database =======================")
            # Load indexer data from database
            docs, lenDoc, docNo, freqWordDoc = self.db.load_indexer_data()
            invInd = self.db.load_inverted_index()

            print(docs)
            print(lenDoc)
            print(docNo)
            print(freqWordDoc)
            print(invInd)

            # Create indexer with loaded data
            self.indexer.docs = docs
            self.indexer.lenDoc = lenDoc
            self.indexer.docNo = docNo
            self.indexer.freqWordDoc = freqWordDoc
            self.indexer.invInd = invInd
        else:
            self.crawl_and_index()  # 如果不从数据库加载，则进行爬虫和索引构建

    def crawl_and_index(self):
        # 爬虫部分
        start_url = 'https://www.cse.ust.hk/~kwtleung/COMP4321/testpage.htm'
        num_pages = 10
        spider = GetPage.Spider(start_url, num_pages)
        spider.crawl()
        print("Crawling completed.")

        # 保存抓取的页面到数据库
        self.db.save_pages(spider.pages)
        print("save Crawling completed.")

        # 处理网页数据并索引
        files = []
        for page in spider.pages:
            file = Indexer.File(page)
            files.append(file)

        self.indexer = Indexer.Indexer(files)
        for file in files:
            self.indexer.indexDoc(file.file_id, file.title, file.body)

        # 保存索引数据到数据库
        self.db.save_indexer_data(self.indexer.docs, self.indexer.lenDoc, self.indexer.docNo, self.indexer.freqWordDoc)
        self.db.save_inverted_index(self.indexer.invInd)
        print("finish indexer")

    def search(self, query: str):
        db = Database.Database()
        # 创建搜索引擎实例
        engine = SearchEngine.SearchEngine(self.indexer)

        # 执行预定义的查询
        results = engine.search(query)
        # Convert results to list of (doc_id, score) tuples
        result_tuples = [(doc_id, 1.0) for doc_id in results]  # 使用 1.0 作为默认分数
        db.save_search_results(query, result_tuples)  # 保存搜索结果到数据库
        db.close()
        return self._convert(results)

    def _convert(self, doc_list):
        db = Database.Database()
        # 从数据库加载页面数据
        pages = db.load_pages()  # 假设返回的是一个字典列表
        search_results = []

        # 将 pages 转换为字典以提高查找速度
        # 使用 page_id 作为键，页面字典作为值
        page_dict = {page['page_id']: page for page in pages}

        for doc_id, score in doc_list:
            if doc_id in page_dict:
                page = page_dict[doc_id]
                search_result = SearchRes(
                    page_id=page['page_id'],
                    parent_id=page.get('parent_id'),  # 如果有 parent_id 字段，使用 get() 方法以防 KeyError
                    url=page['url'],
                    title=page['title'],
                    last_modified=page['last_modified'],
                    score=score
                )
                search_results.append(search_result)

        db.close()

        return search_results
