import pandas as pd
import unicodedata
import MeCab
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st

# データフレームの読み込み
df = pd.read_excel('2023-09_kitei_dataframe.xls')

# テキストデータの前処理
df["本文"] = df["本文"].str.normalize("NFKC")

unify_dic = {
    '『': '「',
    '』': '」',
    '【': '「',
    '】': '」'
}

def unify_str(sentence):
    dic_for_unify = str.maketrans(unify_dic)
    sentence = sentence.translate(dic_for_unify)
    return sentence

df["本文"] = df["本文"].apply(unify_str)

# MeCabのインスタンスを作成
mecab = MeCab.Tagger()
mecab.parse("")  # バグ回避

def get_surfaces(text):
    result = []
    node = mecab.parseToNode(text)
    while node:
        if node.feature.startswith("名詞") or node.feature.startswith("動詞"):
            result.append(node.surface)
        node = node.next
    return " ".join(result)

df['text_tokenized'] = df['本文'].apply(get_surfaces)

def split_str(text):
    return text.split(' ')

df['tokenized_split'] = df.text_tokenized.apply(split_str)

def remove_stop_words(sentence):
    stop_words = ["する", "し","こと", "とき", "れ", "(", ")", ".", "%", "さ", "い", "もの", "す", "なら", "係る", "いう", "なら",
                  "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "、",
                  "(", ")",  "等", "前年", "いた", "つき", "なっ"] # 適当な文字を設定
    for s in stop_words:
        sentence = sentence.replace(s, '')
    return sentence

df["text_tokenized1"] = df["text_tokenized"].apply(remove_stop_words)

def n_gram(target, n):
    n_gram_list = [target[idx:idx + n] for idx in range(len(target) - n + 1)]
    return ' '.join([''.join(wordlist) for wordlist in n_gram_list])

df['tokenized_split'] = df.text_tokenized1.apply(split_str)
df['tokenized_2gram'] = df['tokenized_split'].apply(n_gram, n=2)

# テキストデータをTF-IDFベクトルに変換
tfidf_vectorizer = TfidfVectorizer()
tfidf_matrix = tfidf_vectorizer.fit_transform(df['text_tokenized1'].fillna(''))

# TF-IDFベクトルを標準化
ss = StandardScaler(with_mean=False)  # with_meanをFalseに設定
tfidf_matrix_normalized = ss.fit_transform(tfidf_matrix)

# コサイン類似度行列を計算
cos_similarity_matrix = cosine_similarity(tfidf_matrix_normalized)

# Streamlitアプリケーションの開始
st.title("キーワード検索アプリ")

# キーワード入力フィールド
keyword = st.text_input("キーワードを入力してください:")

# キーワードが入力された場合
if keyword:
    # キーワードを前処理
    keyword = unicodedata.normalize("NFKC", keyword)
    keyword = unify_str(keyword)
    keyword = get_surfaces(keyword)
    keyword = remove_stop_words(keyword)

    # 新しいキーワードのTF-IDFベクトルを計算
    new_keyword_tfidf = tfidf_vectorizer.transform([keyword])
    new_keyword_tfidf_normalized = ss.transform(new_keyword_tfidf)

    # コサイン類似度を計算
    cos_similarity_new_keyword = cosine_similarity(new_keyword_tfidf_normalized, tfidf_matrix_normalized)

    # 類似度を含むデータフレームを作成
    df['類似度'] = cos_similarity_new_keyword[0]

    # 類似度でソート
    df = df.sort_values(by='類似度', ascending=False)

    # 結果を表示
    st.subheader("類似度の高い条文:")
    for i, row in df.head(10).iterrows():
        st.write(f"Similarity: {row['類似度']:.4f}")
        st.write(f"保険種名: {row['保険種名']}")
        st.write(f"規程名: {row['規程名']}")
        st.write(f"括弧書き: {row['括弧書き']}")
        st.write(f"条番号: {row['条番号']}")
        st.write(f"本文: {row['本文']}")
        st.write("---")
