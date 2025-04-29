import sqlite3
from typing import List, Dict, Any
import ast


class Database:
    def __init__(self, db_name="search_engine.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()

        # Create pages table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS pages (
            page_id INTEGER PRIMARY KEY,
            url TEXT NOT NULL,
            title TEXT,
            last_modified TEXT,
            body TEXT
        )
        ''')

        # Create inverted_index table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS inverted_index (
            word TEXT NOT NULL,
            doc_id INTEGER NOT NULL,
            title_positions TEXT,
            content_positions TEXT,
            PRIMARY KEY (word, doc_id),
            FOREIGN KEY (doc_id) REFERENCES pages (page_id)
        )
        ''')

        # Create search_results table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_results (
            query TEXT NOT NULL,
            doc_id INTEGER NOT NULL,
            score REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (doc_id) REFERENCES pages (page_id)
        )
        ''')

        # Create docs table to store document information
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS docs (
            doc_id INTEGER PRIMARY KEY,
            title TEXT,
            content TEXT,
            title_words TEXT,
            content_words TEXT,
            FOREIGN KEY (doc_id) REFERENCES pages (page_id)
        )
        ''')

        # Create document_lengths table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS document_lengths (
            doc_id INTEGER PRIMARY KEY,
            length INTEGER NOT NULL,
            FOREIGN KEY (doc_id) REFERENCES pages (page_id)
        )
        ''')

        # Create word_frequencies table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS word_frequencies (
            word TEXT PRIMARY KEY,
            frequency INTEGER NOT NULL
        )
        ''')

        # Create document_count table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS document_count (
            count INTEGER PRIMARY KEY
        )
        ''')

        self.conn.commit()

    def save_pages(self, pages: List[Any]):
        cursor = self.conn.cursor()
        for page in pages:
            cursor.execute('''
            INSERT OR REPLACE INTO pages (page_id, url, title, last_modified, body)
            VALUES (?, ?, ?, ?, ?)
            ''', (page.page_id, page.url, page.title, page.last_modified, page.body))
        self.conn.commit()

    def save_inverted_index(self, inverted_index: Dict[str, Dict[int, Dict[str, List[int]]]]):
        cursor = self.conn.cursor()
        for word, docs in inverted_index.items():
            for doc_id, positions in docs.items():
                cursor.execute('''
                INSERT OR REPLACE INTO inverted_index (word, doc_id, title_positions, content_positions)
                VALUES (?, ?, ?, ?)
                ''', (word, doc_id,
                      str(positions.get('titlePos', [])),
                      str(positions.get('contentPos', []))))
        self.conn.commit()

    def load_inverted_index(self) -> Dict[str, Dict[int, Dict[str, List[int]]]]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM inverted_index')
        
        invInd = {}
        for row in cursor.fetchall():
            word, doc_id, title_positions, content_positions = row
            if word not in invInd:
                invInd[word] = {}
            invInd[word][doc_id] = {
                'titlePos': ast.literal_eval(title_positions),
                'contentPos': ast.literal_eval(content_positions)
            }
        
        return invInd

    def save_search_results(self, query: str, results: List[tuple]):
        cursor = self.conn.cursor()
        for doc_id, score in results:
            cursor.execute('''
            INSERT INTO search_results (query, doc_id, score)
            VALUES (?, ?, ?)
            ''', (query, doc_id, score))
        self.conn.commit()

    def load_search_results(self, query: str = None) -> List[tuple]:
        """
        Load search results from database. If query is provided, load results for that specific query.
        Otherwise load all results.
        Returns list of tuples containing (query, doc_id, score, timestamp)
        """
        cursor = self.conn.cursor()
        
        if query:
            cursor.execute('''
            SELECT query, doc_id, score, timestamp 
            FROM search_results
            WHERE query = ?
            ORDER BY score DESC
            ''', (query,))
        else:
            cursor.execute('''
            SELECT query, doc_id, score, timestamp
            FROM search_results
            ORDER BY query, score DESC
            ''')
            
        return cursor.fetchall()

    def save_indexer_data(self, docs: Dict[int, Dict[str, Any]], lenDoc: Dict[int, int], docNo: int, freqWordDoc: Dict[str, int]):
        cursor = self.conn.cursor()

        # Save docs
        for doc_id, doc_data in docs.items():
            cursor.execute('''
            INSERT OR REPLACE INTO docs (doc_id, title, content, title_words, content_words)
            VALUES (?, ?, ?, ?, ?)
            ''', (doc_id,
                  doc_data['title'],
                  doc_data['content'],
                  str(doc_data['titleWd']),
                  str(doc_data['contentWd'])))

        # Save document lengths
        for doc_id, length in lenDoc.items():
            cursor.execute('''
            INSERT OR REPLACE INTO document_lengths (doc_id, length)
            VALUES (?, ?)
            ''', (doc_id, length))

        # Save word frequencies
        for word, frequency in freqWordDoc.items():
            cursor.execute('''
            INSERT OR REPLACE INTO word_frequencies (word, frequency)
            VALUES (?, ?)
            ''', (word, frequency))

        # Save document count
        cursor.execute('''
        INSERT OR REPLACE INTO document_count (count)
        VALUES (?)
        ''', (docNo,))

        self.conn.commit()

    def load_indexer_data(self) -> tuple[Dict[int, Dict[str, Any]], Dict[int, int], int, Dict[str, int]]:
        cursor = self.conn.cursor()

        # Load docs
        cursor.execute('SELECT * FROM docs')
        docs = {}
        for row in cursor.fetchall():
            doc_id, title, content, title_words, content_words = row
            docs[doc_id] = {
                'title': title,
                'content': content,
                'titleWd': ast.literal_eval(title_words),
                'contentWd': ast.literal_eval(content_words)
            }

        # Load document lengths
        cursor.execute('SELECT * FROM document_lengths')
        lenDoc = {row[0]: row[1] for row in cursor.fetchall()}

        # Load word frequencies
        cursor.execute('SELECT * FROM word_frequencies')
        freqWordDoc = {row[0]: row[1] for row in cursor.fetchall()}

        # Load document count
        cursor.execute('SELECT count FROM document_count')
        docNo = cursor.fetchone()[0]

        return docs, lenDoc, docNo, freqWordDoc

    def load_inverted_index(self) -> Dict[str, Dict[int, Dict[str, List[int]]]]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM inverted_index')

        invInd = {}
        for row in cursor.fetchall():
            word, doc_id, title_positions, content_positions = row
            if word not in invInd:
                invInd[word] = {}
            invInd[word][doc_id] = {
                'titlePos': ast.literal_eval(title_positions),
                'contentPos': ast.literal_eval(content_positions)
            }

        return invInd

    def load_pages(self) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM pages')
        pages = []
        for row in cursor.fetchall():
            page_id, url, title, last_modified, body = row
            pages.append({
                'page_id': page_id,
                'url': url,
                'title': title,
                'last_modified': last_modified,
                'body': body
            })
        return pages

    def close(self):
        self.conn.close()
