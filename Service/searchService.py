# Service/searchService.py
from typing import List

import getPage as GetPage
import indexer as Indexer
import database as Database
import searchEngine as SearchEngine
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class Page:
    def __init__(self, page_id, parent_id, url, title, last_modified, body, size):
        self.page_id = page_id
        self.parent_id = parent_id
        self.url = url
        self.title = title
        self.last_modified = last_modified
        self.body = body  # 新增 body 属性，存储页面内容
        self.size = size  # 新增 size 属性，存储页面大小
        self.child_ids = []  # 存储子页面的ID


class SearchRes:
    def __init__(self, page_id, parent_id, url, title, last_modified, score, size, keywords=None, parent_link=None, child_links=None):
        self.page_id = page_id
        self.parent_id = parent_id
        self.url = url
        self.title = title
        self.last_modified = last_modified
        self.score = score
        self.size = size
        self.keywords = keywords if keywords is not None else {}  # 默认值为一个空字典
        self.parent_link = parent_link  # 单个父链接
        self.child_links = child_links if child_links is not None else []  # 默认值为一个空列表


class SearchService:
    def __init__(self, load_from_db: bool = False):
        self.pages = None
        self.db = Database.Database()
        self.indexer = Indexer.Indexer()

        if load_from_db:
            print("======================= Loading Database =======================")
            # Load indexer data from database
            docs, lenDoc, docNo, freqWordDoc = self.db.load_indexer_data()
            invInd = self.db.load_inverted_index()

            # print(docs)
            # print(lenDoc)
            # print(docNo)
            # print(freqWordDoc)
            # print(invInd)

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
        self.pages = spider.pages
        print("Crawling completed.")

        # 保存抓取的页面到数据库
        self.db.save_pages(spider.pages)
        print("save Crawling completed.")

        files: List[Indexer.File] = []
        for page in spider.pages:
            file = Indexer.File(page)
            files.append(file)
            # print(f"ID: {file.file_id}, Title: {file.title}, Body: {file.body}")
        indexer = Indexer.Indexer()
        for file in files:
            indexer.indexDoc(file.file_id, file.title, file.body)

        # Save indexer data to database
        self.indexer = indexer
        self.db.save_indexer_data(indexer.docs, indexer.lenDoc, indexer.docNo, indexer.freqWordDoc)
        self.db.save_inverted_index(indexer.invInd)
        print("finish indexer")

    def search(self, query: str):
        print("search start")
        db = Database.Database()
        # 创建搜索引擎实例
        engine = SearchEngine.SearchEngine(self.indexer)

        # 执行预定义的查询
        results = engine.search(query)
        # Convert results to list of (doc_id, score) tuples
        result_tuples = [(doc_id, score) for (doc_id, score, wordFreq) in results]
        db.save_search_results(query, result_tuples)
        db.close()
        print("res:")
        print(results)
        # return results
        return self._convert(results)

    def similar_search(self, page_id):
        print("similar search start")
        # 创建搜索引擎实例
        engine = SearchEngine.SearchEngine(self.indexer)

        # 执行预定义的查询
        results = engine.similarSearch(int(page_id))
        # Convert results to list of (doc_id, score) tuples
        # result_tuples = [(doc_id, score) for (doc_id, score, wordFreq) in results]
        print("res:")
        print(results)
        # return results
        return self._convert(results)

    def get_keywords(self):
        db = Database.Database()
        res = db.load_word_frequencies()
        return res



    def get_link(self, id, pages):
        # 遍历 pages 列表，查找匹配的 page_id
        for page in pages:
            if page.page_id == id:
                return page.url  # 返回找到的 Page 对象的 URL
        return None  # 如果没有找到，返回 None

    def _convert(self, scores):
        pages = self.pages
        search_results = []

        # 将 pages 转换为字典以提高查找速度
        # 使用 page_id 作为键，Page 对象作为值
        page_dict = {page.page_id: page for page in pages}

        for doc_id, score, word_freq in scores:
            if doc_id in page_dict:
                page = page_dict[doc_id]
                # keywords_dict = {keyword: info['total'] for keyword, info in word_freq.items()}
                keywords_dict = {keyword: info['total'] for index, (keyword, info) in enumerate(word_freq.items()) if
                               index < 3}

                search_result = SearchRes(
                    page_id=page.page_id,
                    parent_id=page.parent_id,  # 直接从 Page 对象获取 parent_id
                    url=page.url,
                    title=page.title,
                    last_modified=page.last_modified,
                    score=score,
                    size=page.size,  # 使用 Page 对象的 size 属性
                    keywords=keywords_dict,  # 假设 word_freq 是一个字典，例如 {'keyword1': 2, 'keyword2': 3}
                    parent_link=self.get_link(page.parent_id, pages),  # 假设 parent_id 是父链接的 URL
                    child_links=[self.get_link(child_id, pages) for child_id in page.child_ids]  # 获取所有子链接
                )
                search_results.append(search_result)

        return search_results
