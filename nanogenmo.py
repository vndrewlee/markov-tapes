from collections import Counter
import random
import itertools
import datetime

from nltk.corpus import gutenberg
import spacy
import markovify


def doc_to_text(doc):
    """transforms text to be more mergable
    
    1. replaces names and proper nouns
    2. deduplicates consecutive duplicate words
    """

    text_parts = []

    for tok in doc:
        if tok.tag_ == 'NNP':
            new_part = 'someone' + tok.whitespace_
            text_parts.extend(new_part)
        elif tok.tag_ == 'NNPS':
            new_part = 'they' + tok.whitespace_
            text_parts.extend(new_part)
        elif tok.tag_ == 'PRP':
            new_part = 'they' + tok.whitespace_
            text_parts.extend(new_part)
        elif tok.tag_ == 'PRP$':
            new_part = 'their' + tok.whitespace_
            text_parts.extend(new_part)
        else:
            new_part = tok.text_with_ws 
            text_parts.extend(new_part)

    anon_text = ''.join(text_parts)
    
    split_words = anon_text.split(' ')
    no_consec_duplicates = [i[0] for i in itertools.groupby(split_words)] 
    output_text = ' '.join(no_consec_duplicates)

    return(output_text)

sentence_target = 3500

nlp = spacy.load("en_core_web_lg")

nltk_gutenberg_text_names = [
    'austen-emma.txt',
    'austen-persuasion.txt',
    'austen-sense.txt',
    'blake-poems.txt',
    'bryant-stories.txt',
    'burgess-busterbrown.txt',
    'carroll-alice.txt',
    'chesterton-ball.txt',
    'chesterton-brown.txt',
    'chesterton-thursday.txt',
    'edgeworth-parents.txt',
    'milton-paradise.txt',
    'shakespeare-caesar.txt',
    'shakespeare-hamlet.txt',
    'shakespeare-macbeth.txt',
    'whitman-leaves.txt'
]

data = [{'name': name, 'raw': gutenberg.raw(name)} for name in nltk_gutenberg_text_names]

# parse each text document with spacy
for record in data:
    doc = nlp(record['raw'])
    record.update(dict(doc=doc))

# create an alternate text version without pronouns or propernouns
for record in data:
    doc = record['doc']     
    anon_text = doc_to_text(doc)
    record.update(dict(anon_text=anon_text))

for record in data:
    doc = record['doc']

    sents = list(doc.sents)

    sent_texts = [doc_to_text(sent) for sent in sents]

    single_sentence_models = []

    for sent_text in sent_texts:
        try:
            model = markovify.Text(sent_text, state_size=2)
            single_sentence_models.append(model)
        except:
            pass
        
    record['single_sentence_models'] = single_sentence_models

outputs = []

max_len = max([len(record['single_sentence_models']) for record in data])
weights = [len(record['single_sentence_models'])/max_len for record in data]

for i in range(sentence_target):
    progress = i/sentence_target
    end_window_norm = (i+50)/sentence_target
    book_models = []
    for record in data:
        sentence_count = len(record['single_sentence_models'])
        start = int(progress*sentence_count)
        end = int(end_window_norm*sentence_count)
        end = end if end > start else start+1
        combined_model = markovify.combine(record['single_sentence_models'][start:end])
        book_models.append(combined_model)
    multi_model = markovify.combine(book_models, weights)
    new_sent = multi_model.make_sentence(tries=1000)
    if new_sent:
        outputs.append(new_sent)

output_text = ' '.join(outputs)

timestamp = str(int(datetime.datetime.now().timestamp()))
filename = "novel_" + timestamp + ".txt"

with open(filename, "w") as text_file:
    text_file.write(output_text)

print('words', len(output_text.split(' ')))
print('sentences', len(outputs))
print('filename', filename)