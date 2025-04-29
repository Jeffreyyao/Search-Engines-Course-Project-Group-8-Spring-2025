import os
from flask import Flask, request, render_template

from Service.searchService import SearchService

app = Flask(__name__)


# 初始化代码
def initialize(load_from_db: bool):
    print("应用程序初始化")
    search_service = SearchService(load_from_db)  # 传递参数决定是否从数据库加载
    return search_service


# 在这里设置 load_from_db 的值
load_from_db = False  # 根据需要设置为 True 或 False
# load_from_db = True
search_service = initialize(load_from_db)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    search_results = search_service.search(query)  # 执行搜索
    return render_template('results.html', search_results=search_results)


@app.route('/similar_search')
def similar_search():
    page_id = request.args.get('page_id')
    search_results = search_service.similar_search(page_id)  # 执行搜索
    return render_template('similar_res.html', search_results=search_results)


@app.route('/keywords')
def keywords():
    frequencies = search_service.get_keywords()
    # 这里返回关键词列表页面
    return render_template('keywords.html', frequencies=frequencies)  # 假设你有一个 keywords.html 页面


if __name__ == '__main__':
    app.run(debug=False)
