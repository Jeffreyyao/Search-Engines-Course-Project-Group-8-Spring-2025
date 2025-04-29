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
search_service = initialize(load_from_db)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    search_results = search_service.search(query)  # 执行搜索
    print("res is")
    print(search_results)
    return render_template('results.html', search_results=search_results)


if __name__ == '__main__':
    app.run(debug=False)
