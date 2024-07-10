import time

from openai import OpenAI
import pandas as pd
import numpy as np

from env import openai_api_key

client = OpenAI(api_key=openai_api_key)

from sklearn.metrics.pairwise import cosine_similarity

def get_embedding(text, model="text-embedding-3-small"):
    text = text.replace("\n", " ")
    text = text[:2000]
    return client.embeddings.create(input=[text], model=model).data[0].embedding


def embed_df(path):
    df = pd.read_csv(path)
    df["combined"] = df["title"].fillna('') + " " + df["writer"].fillna('') + " " + df["content_text"].fillna('') + df[
        'content_images'].fillna('')
    df['ada_embedding'] = df.combined.apply(lambda x: get_embedding(x, model='text-embedding-3-small'))
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    return df




def load_df_for_search(path):
    df = pd.read_csv(path)
    df['ada_embedding'] = df.ada_embedding.apply(eval).apply(np.array)
    return df


def search_post(df, context, n=3, pprint=True):
    print("Embedding start")
    embedding = get_embedding(context, model='text-embedding-3-small')
    print("Embedding end")
    df['similarities'] = df.ada_embedding.apply(
            lambda x: cosine_similarity(np.array(x).reshape(1, -1), np.array(embedding).reshape(1, -1)))
    res = df.sort_values('similarities', ascending=False).head(n)
    if pprint:
        for idx, row in res.iterrows():
            print(row['title'])
            # print(row['content_text'])
            # print(row['content_images'])
            print(row['similarities'])
            print()
    return res


if __name__ == '__main__':
    # embed_df("").to_csv('embedded_sunrise_post.csv', index=False)
    # df = pd.read_csv('embedded_sunrise_post.csv')
    # res = search_reviews(df, '이번에 확진자가 몇명인데', n=3)

    # combine csv in /input
    import os

    path = 'input'
    files = os.listdir(path)
    df = pd.concat([pd.read_csv(f'{path}/{file}') for file in files], axis=0, ignore_index=True)
    print(df)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df.to_csv('embedded_df_raw.csv', index=False)
    embed_df('embedded_df_raw.csv').to_csv('embedded_df.csv', index=True)

    # df = load_df_for_search('embedded_df.csv')
    # import time
    #
    # start = time.time()
    # res = search_post(df, '연세대 설명회?', n=20)
    # print(time.time() - start)
