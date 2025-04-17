import math
from collections import defaultdict
import re

class SearchEngine:
    def __init__(self):
        self.invInd = defaultdict(dict)  # {word: {docId: [positions]}}
        self.docs = {}  # {docId: {'title': str, 'content': str, 'titleWd': list, 'contentWd': list}}
        self.lenDoc = {}  # {docId: length}
        self.docNo = 0
        self.freqWordDoc = defaultdict(int)  # {word: number of docs containing word}
    
    def preText(self, words):
        return re.findall(r'\b\w+\b', words.lower())
    
    def indexDoc(self, docID, title, content):
        titleWd = self.preText(title)
        contentWd = self.preText(content)
        self.docNo += 1
        self.docs[docID] = {
            'title': title,
            'content': content,
            'titleWd': titleWd,
            'contentWd': contentWd
        }
        for position, word in enumerate(titleWd):
            if docID not in self.invInd[word]:
                self.invInd[word][docID] = {'titlePos': [], 'contentPos': []}
                self.freqWordDoc[word] += 1
            self.invInd[word][docID]['titlePos'].append(position)
        for position, word in enumerate(contentWd):
            if docID not in self.invInd[word]:
                self.invInd[word][docID] = {'titlePos': [], 'contentPos': []}
                self.freqWordDoc[word] += 1
            self.invInd[word][docID]['contentPos'].append(position)
        self.lenDoc[docID] = self.findLenDoc(docID)
    
    def findLenDoc(self, docId):
        doc_info = self.docs[docId]
        allWd = doc_info['titleWd'] + doc_info['contentWd']
        wdWeights = {}
        for word in set(allWd):
            tf = allWd.count(word)
            tfMax = max([allWd.count(t) for t in set(allWd)] or [1])
            idf = math.log(self.docNo / (self.freqWordDoc[word] or 1))
            wdWeights[word] = idf* (tf / tfMax) 
        len1 = 0
        for w in wdWeights.values():
            len1 += w**2
        return math.sqrt(len1) 
    
    def search(self, query, maxResults=50):
        phMatched = re.findall(r'"([^"]+)"', query)
        remaining_query = re.sub(r'"[^"]+"', '', query).strip()
        allWd = []
        for phrase in phMatched:
            allWd.extend(self.preText(phrase))
        if remaining_query:
            allWd.extend(self.preText(remaining_query))
        if not allWd:
            return []
        candidate_docs = set()
        for word in allWd:
            if word in self.invInd:
                candidate_docs.update(self.invInd[word].keys())
        scores = []
        for docId in candidate_docs:
            score = self.calculate_doc_score(docId, allWd, phMatched)
            scores.append((docId, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return [docId for docId, score in scores[:maxResults]]
    
    def calculate_doc_score(self, docId, Qwd, phMatched):
        doc_info = self.docs[docId]
        allDocWd = doc_info['titleWd'] + doc_info['contentWd']
        wQ = {}
        for word in set(Qwd):
            tf_query = Qwd.count(word)
            idf = math.log(self.docNo / (self.freqWordDoc.get(word, 1) or 1))
            wQ[word] = tf_query * idf
        wDoc = {}
        for word in set(allDocWd):
            tf_doc = allDocWd.count(word)
            tfMax = max([allDocWd.count(t) for t in set(allDocWd)] or [1])
            idf = math.log(self.docNo / (self.freqWordDoc.get(word, 1) or 1))
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
        lenDoc = self.lenDoc[docId]
        if lenQ == 0 or lenDoc == 0:
            return 0
        cosSim = dotProduct / (lenQ * lenDoc)
        for phrase in phMatched:
            phWd = self.preText(phrase)
            if self.check_phrase_in_doc(docId, phWd):
                cosSim *= 1.5  
        return cosSim
    
    def check_phrase_in_doc(self, docId, phWd):
        if len(phWd) == 0:
            return False
        for word in phWd:
            if word not in self.invInd or docId not in self.invInd[word]:
                return False
        titlePos = []
        for i, word in enumerate(phWd):
            positions = self.invInd[word][docId]['titlePos']
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
            positions = self.invInd[word][docId]['contentPos']
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

# Example only
if __name__ == "__main__":
    engine = SearchEngine()
    
    # Index some docs, should be importing from DB instead
    engine.indexDoc(1, "Hong Kong Universities", "Hong Kong has several prestigious universities including HKUST.")
    engine.indexDoc(2, "Chinese Universities", "China has many top universities such as Tsinghua and Peking University.")
    engine.indexDoc(3, "Education in Hong Kong", "The education system in Hong Kong is competitive with many international schools.")
    
    # Perform searches
    print("Search for 'hong kong':", engine.search("hong kong"))
    print("Search for phrase '\"science\"':", engine.search('"science"'))
    print("Search for 'universities':", engine.search("universities"))
    print("Search for 'hong kong universities':", engine.search("hong kong universities"))