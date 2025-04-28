import math, re
from collections import defaultdict
from typing import List

class Porter:
    def __init__(self):
        pass

    def clean(self, s):
        """Remove non-alphanumeric characters from the string."""
        return ''.join(c for c in s if c.isalnum())

    def has_suffix(self, word, suffix, stem):
        """Check if word has the given suffix and return the stem if it does."""
        if len(word) <= len(suffix):
            return False
        if len(suffix) > 1:
            if word[-2] != suffix[-2]:
                return False

        stem.str = word[:-len(suffix)]
        return word == stem.str + suffix

    def vowel(self, ch, prev):
        """Check if character is a vowel."""
        if ch in ['a', 'e', 'i', 'o', 'u']:
            return True
        if ch == 'y':
            return prev not in ['a', 'e', 'i', 'o', 'u']
        return False

    def measure(self, stem):
        """Count the number of VC sequences in the stem."""
        count = 0
        i = 0
        length = len(stem)

        while i < length:
            # Find next vowel
            while i < length:
                if i > 0:
                    if self.vowel(stem[i], stem[i-1]):
                        break
                else:
                    if self.vowel(stem[i], 'a'):
                        break
                i += 1

            # Find next consonant
            i += 1
            while i < length:
                if i > 0:
                    if not self.vowel(stem[i], stem[i-1]):
                        break
                else:
                    if not self.vowel(stem[i], '?'):
                        break
                i += 1

            if i < length:
                count += 1
                i += 1

        return count

    def contains_vowel(self, word):
        """Check if word contains a vowel."""
        for i in range(len(word)):
            if i > 0:
                if self.vowel(word[i], word[i-1]):
                    return True
            else:
                if self.vowel(word[0], 'a'):
                    return True
        return False

    def cvc(self, s):
        """Check if stem has consonant-vowel-consonant pattern."""
        length = len(s)
        if length < 3:
            return False

        if (not self.vowel(s[-1], s[-2]) and
            s[-1] not in ['w', 'x', 'y'] and
            self.vowel(s[-2], s[-3])):
            if length == 3:
                return not self.vowel(s[0], '?')
            else:
                return not self.vowel(s[-3], s[-4])
        return False

    def step1(self, s):
        """Step 1 of the Porter algorithm."""
        stem = type('', (), {'str': ''})()

        if s.endswith('s'):
            if self.has_suffix(s, 'sses', stem) or self.has_suffix(s, 'ies', stem):
                s = s[:-2]
            else:
                if len(s) == 1 and s[-1] == 's':
                    return ''
                if s[-2] != 's':
                    s = s[:-1]

        if self.has_suffix(s, 'eed', stem):
            if self.measure(stem.str) > 0:
                s = s[:-1]
        else:
            if (self.has_suffix(s, 'ed', stem) or self.has_suffix(s, 'ing', stem)):
                if self.contains_vowel(stem.str):
                    s = stem.str
                    if len(s) == 1:
                        return s

                    if (self.has_suffix(s, 'at', stem) or
                        self.has_suffix(s, 'bl', stem) or
                        self.has_suffix(s, 'iz', stem)):
                        s += 'e'
                    else:
                        length = len(s)
                        if (s[-1] == s[-2] and
                            s[-1] not in ['l', 's', 'z']):
                            s = s[:-1]
                        elif self.measure(s) == 1 and self.cvc(s):
                            s += 'e'

        if self.has_suffix(s, 'y', stem):
            if self.contains_vowel(stem.str):
                s = stem.str + 'i'
        return s

    def step2(self, s):
        """Step 2 of the Porter algorithm."""
        suffixes = [
            ('ational', 'ate'),
            ('tional', 'tion'),
            ('enci', 'ence'),
            ('anci', 'ance'),
            ('izer', 'ize'),
            ('iser', 'ize'),
            ('abli', 'able'),
            ('alli', 'al'),
            ('entli', 'ent'),
            ('eli', 'e'),
            ('ousli', 'ous'),
            ('ization', 'ize'),
            ('isation', 'ize'),
            ('ation', 'ate'),
            ('ator', 'ate'),
            ('alism', 'al'),
            ('iveness', 'ive'),
            ('fulness', 'ful'),
            ('ousness', 'ous'),
            ('aliti', 'al'),
            ('iviti', 'ive'),
            ('biliti', 'ble')
        ]

        stem = type('', (), {'str': ''})()
        for suffix, replacement in suffixes:
            if self.has_suffix(s, suffix, stem):
                if self.measure(stem.str) > 0:
                    return stem.str + replacement
        return s

    def step3(self, s):
        """Step 3 of the Porter algorithm."""
        suffixes = [
            ('icate', 'ic'),
            ('ative', ''),
            ('alize', 'al'),
            ('alise', 'al'),
            ('iciti', 'ic'),
            ('ical', 'ic'),
            ('ful', ''),
            ('ness', '')
        ]

        stem = type('', (), {'str': ''})()
        for suffix, replacement in suffixes:
            if self.has_suffix(s, suffix, stem):
                if self.measure(stem.str) > 0:
                    return stem.str + replacement
        return s

    def step4(self, s):
        """Step 4 of the Porter algorithm."""
        suffixes = [
            'al', 'ance', 'ence', 'er', 'ic', 'able', 'ible', 'ant',
            'ement', 'ment', 'ent', 'sion', 'tion', 'ou', 'ism', 'ate',
            'iti', 'ous', 'ive', 'ize', 'ise'
        ]

        stem = type('', (), {'str': ''})()
        for suffix in suffixes:
            if self.has_suffix(s, suffix, stem):
                if self.measure(stem.str) > 1:
                    return stem.str
        return s

    def step5(self, s):
        """Step 5 of the Porter algorithm."""
        if s.endswith('e'):
            if self.measure(s) > 1:
                s = s[:-1]
            elif self.measure(s) == 1:
                stem = s[:-1]
                if not self.cvc(stem):
                    s = stem

        if len(s) == 1:
            return s

        if (s.endswith('ll') and self.measure(s) > 1):
            s = s[:-1]

        return s

    def strip_prefixes(self, s):
        """Remove common prefixes."""
        prefixes = [
            'kilo', 'micro', 'milli', 'intra', 'ultra',
            'mega', 'nano', 'pico', 'pseudo'
        ]

        for prefix in prefixes:
            if s.startswith(prefix):
                return s[len(prefix):]
        return s

    def strip_suffixes(self, s):
        """Apply all suffix stripping steps."""
        s = self.step1(s)
        if len(s) >= 1:
            s = self.step2(s)
        if len(s) >= 1:
            s = self.step3(s)
        if len(s) >= 1:
            s = self.step4(s)
        if len(s) >= 1:
            s = self.step5(s)
        return s

    def strip_affixes(self, s):
        """Main method to stem a word."""
        s = s.lower()
        s = self.clean(s)

        if s and len(s) > 2:
            s = self.strip_prefixes(s)
            if s:
                s = self.strip_suffixes(s)

        return s

import getPage as GetPage

class File:
    def __init__(self, page: GetPage.Page):
        self.page = page
        self.porter = Porter()
        self.title = " ".join(self.stem(self.stop(page.title.split())))
        self.body = " ".join(self.stem(self.stop(page.body.split())))
        self.file_id = page.page_id

    def __repr__(self):
        return f"File[{self.file_id}]"
    
    def stop(self, text_list: List[str]):
        stopwords = set(open("stopwords.txt").read().split("\n"))
        return [word.lower() for word in text_list if word.lower() not in stopwords]
    
    def stem(self, text_list: List[str]):
        return [self.porter.strip_affixes(word) for word in text_list]
    
class Indexer:
    def __init__(self, files: List[File]):
        self.invInd = defaultdict(dict) 
        self.docs = {}  
        self.lenDoc = {}  
        self.docNo = 0
        self.freqWordDoc = defaultdict(int)

    def preText(self, words):
        return re.findall(r'\b\w+\b', words.lower())
    
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

if __name__ == "__main__":
    file1 = File("This is the Test page for a crawler", "Before getting the Admission of CSE department of HKUST, You should read through these international news and these books.")
    file2 = File("CSE department of HKUST", "PG Admission UG Admission Back to main")
    indexer = Indexer([file1, file2])
    indexer.index()
