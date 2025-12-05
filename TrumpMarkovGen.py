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
            line = 'Line:: ' + line   # Adds sentinel
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
def end_punc_check(text):
    punctuation_symbols = ('.', '!', '?')
    honorifics = {
        'mr.', 'ms.', 'mrs.', 'mx.', 'dr.', 'prof.', 'capt.', 'gen.', 'gov.',
        'sen.', 'st.', 'rev.', 'hon.', 'jr.', 'sr.', 'ph.d.', 'phd.', 'm.d.',
        'b.a.', 'm.a.', 'd.d.s.'
    }
    other_abbreviations = {
        'etc.', 'a.m.', 'p.m.', 'vol.', 'inc.', 'co.', 'corp.', 'ltd.', 'www.'
    }
    repeating_symbols = {'.' : 2, ',' : 2}  # Symbol: minimum repetitions

    # Trim trailing quotes/brackets
    word = text.strip().rstrip('"\')]}').lower()

    # Check honorifics and common abbreviations
    if word in honorifics or word in other_abbreviations:
        return False
    
    # Check for repeating symbols
    for symbol, min_count in repeating_symbols.items():
        if symbol * min_count in word:
            return False

    # True only if the cleaned word ends in . ! or ?
    return word.endswith(punctuation_symbols)


# Filter paired punctuation
    # Always place pairs that contain another punctuation first
homo_punc = ['"', '\'', '\\*', '**', '*', '`', '~~', '__', ':']   # Homogenous pairs have identical opens and closes
hetero_punc = [('(<', '>)'), ('(', ')'), ('[', ']'), ('{', '}')]   # Heterogenous pairs have different opens and closes
any_text = fr'?<=[A-Za-z0-9.?!]'

def paired_punc_filter(text, w):
    prospective = text + f' {w}'
    
    # Homogenous pairs
    for i in homo_punc:
        punc_ends = fr'({any_text}{re.escape(i)})'
        if prospective.count(i) % 2 != 0:
            if re.search(punc_ends, w):
                w = re.sub(punc_ends, '', w)   # Removes only the punctuation character
    
    # Heterogenous pairs
    for open_char, close_char in hetero_punc:
        open_count = prospective.count(open_char)
        close_count = prospective.count(close_char)
        
        if open_count > close_count + 1:   # Excess opens
            punc_start = fr'({any_text}){re.escape(open_char)}'
            if re.search(punc_start, w):
                w = re.sub(punc_start, '', w)   # Removes only the punctuation character
                
        elif close_count > open_count:   # Excess closes
            punc_end = fr'{re.escape(close_char)}({any_text})'
            if re.search(punc_end, w):
                w = re.sub(punc_end, '', w)   # Removes only the punctuation character
    
    return w


# End with closed punctuation pairs
def paired_punc_close(text, w):
    for i in homo_punc:
        if text.count(i) % 2 != 0 and end_punc_check(w):
            text += i


#-------------------------


# Generate text
def generatetext(chain):
    memory_max = len(list(chain.keys())[-1])
        
    # Start with sentinel
    text = 'Line::'
        
    while True:
        # Select up to the largest possible section of text within 'memory_cap' for as a key candidate
        key = [] 
        words = text.split()
        
        for i in range(1, memory_max + 1):
            if len(words) >= i:
                memory = tuple(words[-i:])
                if memory in chain:
                    key = (chain[memory])
                
        # If no key found, restart text generation
        if not key:
            text = 'Line::'
            continue
        
        w = paired_punc_filter(text, random.choice(key))
        text += f' {w}'
    

            
        # Break conditions:
        # - if the sentinel appears beyond the starting sentinel
        # - if the text is long and the chosen word ends a sentence
        if text.count('Line::') > 1 or (len(text) > 200 and end_punc_check(w)):
            text = text.replace('Line:: ', '').replace('Line::', '')
            if text.count('"') % 2 != 0:
                text += '"'
                text = text[:-2] + text[-1]
            break
    
    return text


#-------------------------


# Main execution
url = 'https://raw.githubusercontent.com/ryanmcdermott/trump-speeches/master/speeches.txt'
words = fetch_process_data(url)
chain = build_chain(words, 3)

print('Corpus size: {0} words.'.format(len(words)))
print('Chain size: {0} distinct word groups.'.format(len(chain)))

print(generatetext(chain))

# Repeating and debug utilities
data_recall = {
    'chain': chain,
    'corpus': words,
    'url': url
}

while True:
    prompt = input('')
    
    # Index search
    if not re.match('::', prompt) and prompt != '':
        key = tuple(prompt.split())

        if key in chain:
            print(f'{key} -> {chain[key]}')
        else:
            print('Index not found')

    else:
        print(generatetext(chain))
