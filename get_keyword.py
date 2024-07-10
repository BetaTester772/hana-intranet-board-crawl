from konlpy.tag import Okt, Kkma
import time
import pandas as pd
from krwordrank.word import summarize_with_keywords

import re


def split_noun_sentences(text):
    okt = Okt()
    sentences = text.replace(". ", ".")
    sentences = re.sub(r'([^\n\s\.\?!]+[^\n\.\?!]*[\.\?!])', r'\1\n', sentences).strip().split("\n")

    result = []
    for sentence in sentences:
        if len(sentence) == 0:
            continue
        sentence_pos = okt.pos(sentence, stem=True)
        print(sentence_pos)
        nouns = [word for word, pos in sentence_pos if pos == 'Noun']
        if len(nouns) == 1:
            continue
        result.append(' '.join(nouns) + '.')

    return result


def split_words(text, pos_=None):
    okt = Okt()
    if pos_:
        sentence_pos = okt.pos(text, stem=True)
        words = [word for word, pos in sentence_pos if pos == pos_]
    else:
        words = okt.morphs(text, norm=True)
    return ' '.join(words)


def get_keyword_from_pd_row(row: pd.DataFrame) -> list:
    result = []
    # print(row['combined'])
    # print("=" * 50)

    try:
        keywords = summarize_with_keywords([split_words(row['combined'])], min_count=2)
    except:
        # print(row['title'])
        keywords = summarize_with_keywords([split_words(row['combined'])], min_count=1)
    for word, r in keywords.items():
        result.append(word)
        if len(result) > 5:
            break

    if row['title'].startswith('['):
        sub_title = row['title'].split(']', 1)[0][1:].strip()
        result.append(sub_title)

    if row['writer']:
        result.append(row['writer'])

    return result


def find_word_from_df_keyword(df: pd.DataFrame, word: str):
    result = []
    for i in range(len(df)):
        if word in df.iloc[i]['keywords'] or word in df.iloc[i]['title']:
            result.append(df.iloc[i])
    return result


def add_keyword_on_df(df: pd.DataFrame):
    keywords = []

    for i in range(len(df)):
        keywords.append(get_keyword_from_pd_row(df.iloc[i]))

    df['keywords'] = keywords
    return df


if __name__ == '__main__':
    import time

    df = pd.read_csv('embedded_df.csv')

    df = add_keyword_on_df(df)

    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df.to_csv('embedded_df_with_keywords.csv', index=True)

    df = pd.read_csv('embedded_df_with_keywords.csv')

    start_time = time.time()
    result = find_word_from_df_keyword(df, '연세대')
    print("time :", time.time() - start_time)

    for i in range(len(result)):
        print(result[i]['title'])
        print(result[i]['keywords'])
        print()
