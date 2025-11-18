# Trump tweet generator markov chain

import urllib.request
import random
import re

# Fetch and process the corpus data
def fetch_process_data(url):
    text = urllib.request.urlopen(url)
    words = []
    
    # Processes the data line-by-line
    for line in text:
        line = line.decode('utf-8').replace('\r', ' ').replace('\n', ' ')
        if line.strip():   # Skips empty lines
            line = 'Line::: ' + line   # Adds sentinel
            new_words = line.split(' ')
            new_words = [word for word in new_words if word not in ['', ' ']]   # Removes empty strings and spaces
            words += new_words
                
    return words


# Build the chain
def build_chain(words, memory_cap = 1):
    chain = {}
    
    # Creates chains of every length up to the cap
    for memory in range(1, memory_cap + 1):
        for i in range(len(words) - memory):
            key = tuple(words[i:i + memory])
            word = words[i + memory]
            chain.setdefault(key, []).append(word)
        
        # Removes chains with too few indexes for their memory
        chain = {key: value for key, value in chain.items() if len(value) >= (len(key) // 2)}
        
    return chain

# Check for sentence-ending punctuation
def punctuation_check(text):
    punctuation_symbols = ('.', '!', '?')
    honorifics = {
        'mr.', 'ms.', 'mrs.', 'mx.', 'dr.', 'prof.', 'capt.', 'gen.', 'gov.',
        'sen.', 'st.', 'rev.', 'hon.', 'jr.', 'sr.', 'ph.d.', 'phd.', 'm.d.',
        'b.a.', 'm.a.', 'd.d.s.'
    }
    other_abbreviations = {
        'etc.', 'a.m.', 'p.m.', '...', 'vol.', 'inc.', 'co.', 'corp.', 'ltd.', 'www.'
    }

    # Trim trailing quotes/brackets
    word = text.strip().rstrip('"\')]}').lower()

    # Excepts honorifics and common abbreviations
    if word in honorifics or word in other_abbreviations:
        return False

    # True only if the cleaned word ends in . ! or ?
    return word.endswith(punctuation_symbols)


# Generate a tweet
def generateTweet(chain):
    memory_max = len(list(chain.keys())[-1])
        
    # Start with sentinel
    tweet = 'Line:::'
        
    while True:
        # Select up to the largest possible section of text within 'memory_cap' for as a key candidate
        key = [] 
        words = tweet.split()
        
        for i in range(1, memory_max + 1):
            if len(words) >= i:
                memory = tuple(words[-i:])
                if memory in chain:
                    key = (chain[memory])
                
        # If no key found, restart tweet generation
        if not key:
            tweet = 'Line:::'
            continue
        
        w = random.choice(key)
        
        # Remove punctuation-adjacent paired punctuation marks when necessary
        prospective = tweet + f' {w}'
        
        homo_punc = ['"', '\'']   # Homogenous punctuation
        hetero_punc = [('(', ')'), ('[', ']'), ('{', '}')]   # Heterogenous punctuation
        
        for i in homo_punc:
            punc_ends = fr'?<=[A-Za-z0-9.?!]{re.escape(i)}'
            if prospective.count(i) % 2 != 0:
                if re.search(punc_ends, w):
                    w = re.sub(punc_ends, '', w)   # Removes only the punctuation character
        
        for open_char, close_char in hetero_punc:
            open_count = prospective.count(open_char)
            close_count = prospective.count(close_char)
            
            if open_count > close_count:  # More opens than closes
                punc_start = fr'(?<=[A-Za-z0-9.?!]){re.escape(open_char)}'
                if re.search(punc_start, w):
                    w = re.sub(punc_start, '', w)
            elif close_count > open_count:  # More closes than opens
                punc_end = fr'{re.escape(close_char)}(?=[A-Za-z0-9.?!])'
                if re.search(punc_end, w):
                    w = re.sub(punc_end, '', w)

        tweet += f' {w}'
    
        # Adds closing quotes if needed
        if tweet.count('"') % 2 != 0 and punctuation_check(w):
            tweet += '"'
            
        # Break conditions:
        # - if the sentinel appears beyond the starting sentinel
        # - if the tweet is long and the chosen word ends a sentence
        if tweet.count('Line:::') > 1 or (len(tweet) > 200 and punctuation_check(w)):
            tweet = tweet.replace('Line::: ', '').replace('Line:::', '')
            if tweet.count('"') % 2 != 0:
                tweet += '"'
                tweet = tweet[:-2] + tweet[-1]
            break
    
    return tweet


# Main execution
url = 'https://raw.githubusercontent.com/ryanmcdermott/trump-speeches/master/speeches.txt'
words = fetch_process_data(url)
chain = build_chain(words, 3)

print('Corpus size: {0} words.'.format(len(words)))
print('Chain size: {0} distinct word groups.'.format(len(chain)))

print(generateTweet(chain))

# Repeating and debug utilities
while True:
    prompt = input("")
    if prompt == ':::chain':
        print(chain)
    elif prompt != '':
        if (prompt) in chain:
            print(chain[(prompt)])
        else:
            print('Index not found')
    else:
        print(generateTweet(chain))
