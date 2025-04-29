Search Engine Course Project - Group 8

Project Description:
This is a search engine implementation that includes web crawling, indexing, and search functionality. The project consists of several components:
- Web page retrieval (getPage.py)
- Indexing system (indexer.py)
- Search engine implementation (searchEngine.py)
- Database management (database.py)
- Main application (app.py)
- Request processing service (Service)
- Front end page (templates)

Dependencies:
- Python 3.x
- SQLite3 (built-in with Python)
- Required Python packages:
  - requests
  - beautifulsoup4
  - Flask

Setup Instructions:
1. Create and activate a virtual environment:
   python -m venv venv
   source venv/bin/activate  # On Unix/macOS
   # OR
   venv\Scripts\activate  # On Windows

2. Install required packages:
   pip install requests beautifulsoup4
   pip install Flask

Running the Project:
1. To run the search engine with a fresh database:
   python app.py

2. To run the search engine using existing database:
   python main.py --load-db

3. The search engine will prompt you to enter search queries interactively.

Project Structure:
- app.py: Main application entry point
- Service: Handling various requests
- templates: Front end page
- getPage.py: Web page retrieval and parsing
- indexer.py: Document indexing system
- searchEngine.py: Search functionality implementation
- database.py: Database management and storage
- search_engine.db: SQLite database file
- stopwords.txt: List of stopwords for text processing

Note: The project uses SQLite for data storage, and the database file (search_engine.db) will be created automatically when running the application for the first time.
