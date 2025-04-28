import math
from collections import defaultdict
import re

import indexer as Indexer

class SearchEngine:
    def __init__(self, indexer: Indexer): 
        self.indexer = indexer
    
    def search(self, query, maxResults=50):
        porter = Indexer.Porter()
        query = " ".join([porter.strip_affixes(word) for word in query.split()])
        phMatched = re.findall(r'"([^"]+)"', query)
        remaining_query = re.sub(r'"[^"]+"', '', query).strip()
        allWd = []
        for phrase in phMatched:
            allWd.extend(self.indexer.preText(phrase))
        if remaining_query:
            allWd.extend(self.indexer.preText(remaining_query))
        if not allWd:
            return []
        candidate_docs = set()
        for word in allWd:
            if word in self.indexer.invInd:
                candidate_docs.update(self.indexer.invInd[word].keys())
        scores = []
        for docId in candidate_docs:
            score, wordFreq = self.calculate_doc_score(docId, allWd, phMatched)
            scores.append((docId, score, wordFreq))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:maxResults]
    
    def calculate_doc_score(self, docId, Qwd, phMatched):
        doc_info = self.indexer.docs[docId]
        allDocWd = doc_info['titleWd'] + doc_info['contentWd']
        wordFreq = {}
        for word in set(allDocWd):
            wordFreq[word] = {
                'total': allDocWd.count(word),
                'title': doc_info['titleWd'].count(word),
                'content': doc_info['contentWd'].count(word)
            }
        wQ = {}
        for word in set(Qwd):
            tf_query = Qwd.count(word)
            idf = math.log(self.indexer.docNo / (self.indexer.freqWordDoc.get(word, 1) or 1))
            wQ[word] = tf_query * idf
        wDoc = {}
        for word in set(allDocWd):
            tf_doc = allDocWd.count(word)
            tfMax = max([allDocWd.count(t) for t in set(allDocWd)] or [1])
            idf = math.log(self.indexer.docNo / (self.indexer.freqWordDoc.get(word, 1) or 1))
            wB = (tf_doc / tfMax) * idf  
            titleNo = doc_info['titleWd'].count(word)
            if titleNo > 0:
                wB *= 2  
            wDoc[word] = wB
        dotProduct = 0
        for word in set(Qwd):
            if word in wDoc:
                dotProduct += wQ[word] * wDoc[word]
        lenQ = math.sqrt(sum(w**2 for w in wQ.values()))
        lenDoc = self.indexer.lenDoc[docId]
        if lenQ == 0 or lenDoc == 0:
            return 0, wordFreq
        cosSim = dotProduct / (lenQ * lenDoc)
        for phrase in phMatched:
            phWd = self.indexer.preText(phrase)
            if self.check_phrase_in_doc(docId, phWd):
                cosSim *= 1.5  
        return cosSim, wordFreq
    
    def check_phrase_in_doc(self, docId, phWd):
        if len(phWd) == 0:
            return False
        for word in phWd:
            if word not in self.indexer.invInd or docId not in self.indexer.invInd[word]:
                return False
        titlePos = []
        for i, word in enumerate(phWd):
            positions = self.indexer.invInd[word][docId]['titlePos']
            if i == 0:
                titlePos = positions
            else:
                new_positions = []
                for position in positions:
                    if position - 1 in titlePos:
                        new_positions.append(position)
                titlePos = new_positions
                if not titlePos:
                    break        
        if titlePos:
            return True
        contentPos = []
        for i, word in enumerate(phWd):
            positions = self.indexer.invInd[word][docId]['contentPos']
            if i == 0:
                contentPos = positions
            else:
                new_positions = []
                for position in positions:
                    if position - 1 in contentPos:
                        new_positions.append(position)
                contentPos = new_positions
                if not contentPos:
                    break
        return bool(contentPos)
        
    def similarSearch(self, docId, originalQ=None, maxAns=50):
        stop_words = {'a', 'about', 'an', 'and', 'are', 'as', 'at', 'be', 'been', 'being', 'but', 'by', 
        'can', 'could', 'did', 'do', 'does', 'down', 'for', 'from', 'had', 'has', 'have',
        'his', 'in', 'into', 'is', 'it', 'its', 'may', 'might', 'must', 'of', 'on', 'or',
        'out', 'over', 'shall', 'should', 'the', 'their', 'them', 'these', 'they', 'this',
        'those', 'to', 'under', 'up', 'was', 'were', 'will', 'with', 'would'
        }
        doc_info = self.indexer.docs[docId]
        allwd = doc_info['titleWd'] + doc_info['contentWd']
        wdCounts = Counter()
        for wd in allwd:
            if (wd not in stop_words and len(wd) > 2 and wd.isalpha() and wd.lower() == wd): 
                wdCounts[wd] += 1
        topSearch = [wd for wd, count in wdCounts.most_common(5)]
        if not topSearch:
            return []
        if originalQ:
            originalSearch = []  
            for t in self.indexer.preText(originalQ):  
                if t not in stop_words and len(t) > 2:  
                    originalSearch.append(t)  
            combinedSearch = list(set(originalSearch + topSearch))
            newQ = ' '.join(combinedSearch)
        else:
            newQ = ' '.join(topSearch)
        similarSearch = self.search(newQ, maxAns)
        newSearch = []
        for doc in similarSearch:
            if doc != docId:
                newSearch.append(doc)
        similarSearch = newSearch
        
        return similarSearch[:maxAns]

# Example only
if __name__ == "__main__":
    engine = SearchEngine()
    
    # Index some docs, should be importing from DB instead
    engine.indexDoc(1, "Hong Kong Universities", "Hong Kong has several prestigious universities including HKUST.")
    engine.indexDoc(2, "Chinese Universities", "China has many top universities such as Tsinghua and Peking University.")
    engine.indexDoc(3, "Education in Hong Kong", "The education system in Hong Kong is competitive with many international schools.")
    engine.indexDoc(4, "Top Asian Universities", "Asian universities like HKU, HKUST, Tsinghua, and NUS are among the best in the world.")
    engine.indexDoc(5, "University Rankings", "Global university rankings often feature institutions from Hong Kong and China prominently.")
    
    # Perform searches
    print("Search for 'hong kong':", engine.search("hong kong"))
    print("Search for phrase '\"science\"':", engine.search('"science"'))
    print("Search for 'universities':", engine.search("universities"))
    print("Search for 'hong kong universities':", engine.search("hong kong universities"))
    if engine.search("hong kong universities"):
        similar_pages = engine.similarSearch(engine.search("hong kong universities")[0], "hong kong universities")
        print("\nSimilar pages to document", engine.search("hong kong universities")[0], ":", similar_pages)
