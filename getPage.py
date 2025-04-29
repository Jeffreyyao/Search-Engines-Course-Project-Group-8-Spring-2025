import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
import os
from concurrent.futures import ThreadPoolExecutor, as_completed


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

    def __repr__(self):
        return (f"Page(id={self.page_id}, parent_id={self.parent_id}, url='{self.url}', "
                f"title='{self.title}', last_modified='{self.last_modified}', body='{self.body[:10]}...', "
                f"size={self.size}, child_ids={self.child_ids})")


class Spider:
    def __init__(self, start_url, num_pages):
        self.start_url = start_url
        self.num_pages = num_pages
        self.visited = set()
        self.page_index = {}
        self.parent_child = {}
        self.id_to_url = {}  # ID 和 URL 的对应关系
        self.inverted_index = {}  # 倒排索引
        self.queue = deque([start_url])
        self.page_id_counter = 0
        self.pages = []  # 用于存储页面对象

    def fetch_page(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for bad responses
            return response.text, response.headers.get('Last-Modified')
        except (requests.RequestException, ValueError):
            return None, None

    def extract_text(self, html):
        """提取页面的文本内容"""
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text(strip=True)  # 提取并返回文本内容

    def extract_links(self, html, base_url):
        soup = BeautifulSoup(html, 'html.parser')
        links = set()
        for a_tag in soup.find_all('a', href=True):
            full_url = urljoin(base_url, a_tag['href'])
            if self.is_same_domain(full_url):
                links.add(full_url)
        return links

    def is_same_domain(self, url):
        return urlparse(url).netloc == urlparse(self.start_url).netloc

    def index_page(self, url, content, last_modified):
        # 检查URL是否已经存在于索引中
        if url in self.page_index:
            return self.page_index[url]['id']  # 如果存在，返回已分配的ID

        # 如果URL不存在，分配新的ID
        page_id = self.page_id_counter
        title = self.extract_title(content)  # 提取页面标题
        body = self.extract_text(content)
        size = len(content)  # 计算页面大小

        self.page_index[url] = {
            'id': page_id,
            'content': content,
            'last_modified': last_modified
        }

        # 保存 ID 和 URL 的对应关系
        self.id_to_url[page_id] = url

        # 创建页面对象并存储
        page = Page(page_id, None, url, title, last_modified, body, size)
        self.pages.append(page)

        # # 保存网页内容到本地文件
        # file_name = f"page_{page_id}.html"  # 使用页面ID作为文件名
        # with open(file_name, 'w', encoding='utf-8') as file:
        #     file.write(content)  # 将网页内容写入文件

        self.page_id_counter += 1
        return page_id

    def extract_title(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        title_tag = soup.find('title')
        return title_tag.string if title_tag else 'No Title'

    def extract_links(self, html, base_url):
        soup = BeautifulSoup(html, 'html.parser')
        links = set()
        link_texts = {}  # 用于存储链接及其对应的文本
        for a_tag in soup.find_all('a', href=True):
            full_url = urljoin(base_url, a_tag['href'])
            if self.is_same_domain(full_url):
                links.add(full_url)
                link_texts[full_url] = a_tag.get_text(strip=True)  # 提取链接文本
        return links, link_texts  # 返回链接和链接文本

    def add_relation(self, parent_id, child_id):
        if parent_id not in self.parent_child:
            self.parent_child[parent_id] = []
        self.parent_child[parent_id].append(child_id)

        # 更新倒排索引
        if child_id not in self.inverted_index:
            self.inverted_index[child_id] = []
        self.inverted_index[child_id].append(parent_id)

        # 更新子页面的父页面ID和子页面ID
        for page in self.pages:
            if page.page_id == child_id:
                page.parent_id = parent_id
                page.child_ids.append(child_id)  # 添加子页面ID
                break

    def crawl(self):
        with ThreadPoolExecutor(max_workers=20) as executor:
            while self.queue and len(self.visited) < self.num_pages:
                current_url = self.queue.popleft()
                if current_url in self.visited:
                    continue

                # 抓取父页面
                future = executor.submit(self.fetch_page, current_url)  # 提交任务
                html, last_modified = future.result()  # 获取结果

                if html is None:
                    continue

                self.visited.add(current_url)
                page_id = self.index_page(current_url, html, last_modified)

                # 提取子链接及其文本
                child_links, link_texts = self.extract_links(html, current_url)

                for link in child_links:
                    if link not in self.visited:
                        if link not in self.page_index or \
                                (self.page_index[link]['last_modified'] and
                                 last_modified and
                                 self.page_index[link]['last_modified'] < last_modified):
                            self.queue.append(link)

                # 处理子链接的抓取
                futures = {executor.submit(self.fetch_page, link): link for link in child_links}  # 提交所有子链接的任务
                for future in as_completed(futures):  # 等待完成
                    link = futures[future]
                    c_html, c_last_modified = future.result()  # 获取结果
                    if c_html is not None:
                        child_id = self.index_page(link, c_html, c_last_modified)
                        # 使用父页面的链接文本作为子页面标题
                        link_title = link_texts.get(link, 'No Title')  # 从父页面的链接文本字典中获取标题
                        self.pages[child_id].title = link_title
                        self.add_relation(page_id, child_id)
        # print(self.pages)


if __name__ == "__main__":
    start_url = 'https://www.cse.ust.hk/~kwtleung/COMP4321/testpage.htm'  # 替换为你的起始 URL
    num_pages = 10  # 设置要索引的页面数量
    spider = Spider(start_url, num_pages)
    spider.crawl()
