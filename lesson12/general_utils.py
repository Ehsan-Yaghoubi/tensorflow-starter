# -*- coding: utf-8 -*-
#
# Copyright 2018 Amir Hadifar. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
import os
import re

import numpy as np
import pandas as pd
from gensim.models import KeyedVectors
from tensorflow import keras

EMBEDDING_CACHE = './data/cache/embedding.npy'
EMBEDDING_FILE = '/Users/mac/PycharmProjects/GrammarCorrection/data/embedding/wiki.en.vec'
CACHE_FILE = './data/cache/'
_MAX_VOCAB = 100000


def load_embedding_matrix(word_index):
    if os.path.isfile(EMBEDDING_CACHE):
        print('---- Load word vectors from cache.')
        embedding_matrix = np.load(open(EMBEDDING_CACHE, 'rb'))
        return embedding_matrix

    print('---- loading embedding ...')
    word2vec = KeyedVectors.load_word2vec_format(EMBEDDING_FILE)
    print('Found %s word vectors of word2vec' % len(word2vec.vocab))

    nb_words = min(_MAX_VOCAB, len(word_index)) + 1

    embedding_matrix = np.zeros((nb_words, 300))
    for word, i in word_index.items():
        if i >= nb_words:
            break
        if word in word2vec.vocab:
            embedding_matrix[i] = word2vec.word_vec(word)
    print('Null word embeddings: %d' % np.sum(np.sum(embedding_matrix, axis=1) == 0))

    np.save(open(EMBEDDING_CACHE, 'wb'), embedding_matrix)
    return embedding_matrix


def _load_x_y(path_file):
    df = pd.read_csv(path_file, sep='\t')
    labels = np.expand_dims(df.is_duplicate.values, axis=1).astype(np.float32)
    q1 = list(df.question1.values.astype(str))
    q2 = list(df.question2.values.astype(str))
    return q1, q2, labels


# The function "text_to_wordlist" is from
# https://www.kaggle.com/currie32/quora-question-pairs/the-importance-of-cleaning-text
def _text_to_wordlist(text):
    # Clean the text, with the option to remove stopwords and to stem words.

    # Convert words to lower case and split them
    text = text.lower().split()

    text = " ".join(text)

    # Clean the text
    text = re.sub(r"[^A-Za-z0-9^,!.\/'+-=]", " ", text)
    text = re.sub(r"what's", "what is ", text)
    text = re.sub(r"\'s", " ", text)
    text = re.sub(r"\'ve", " have ", text)
    text = re.sub(r"can't", "cannot ", text)
    text = re.sub(r"n't", " not ", text)
    text = re.sub(r"i'm", "i am ", text)
    text = re.sub(r"\'re", " are ", text)
    text = re.sub(r"\'d", " would ", text)
    text = re.sub(r"\'ll", " will ", text)
    text = re.sub(r",", " ", text)
    text = re.sub(r"\.", " ", text)
    text = re.sub(r"!", " ! ", text)
    text = re.sub(r"\/", " ", text)
    text = re.sub(r"\^", " ^ ", text)
    text = re.sub(r"\+", " + ", text)
    text = re.sub(r"\-", " - ", text)
    text = re.sub(r"\=", " = ", text)
    text = re.sub(r"'", " ", text)
    text = re.sub(r"(\d+)(k)", r"\g<1>000", text)
    text = re.sub(r":", " : ", text)
    text = re.sub(r" e g ", " eg ", text)
    text = re.sub(r" b g ", " bg ", text)
    text = re.sub(r" u s ", " american ", text)
    text = re.sub(r"\0s", "0", text)
    text = re.sub(r" 9 11 ", "911", text)
    text = re.sub(r"e - mail", "email", text)
    text = re.sub(r"j k", "jk", text)
    text = re.sub(r"\s{2,}", " ", text)

    # Return a list of words
    return text


def _preprocess_texts(texts):
    processed = []
    for t in texts:
        processed.append(_text_to_wordlist(t))
    return processed


def load_data():
    if os.path.isfile(CACHE_FILE + 'q1_train.npy'):  # if cache available
        q1_train = np.load(CACHE_FILE + 'q1_train.npy')
        q2_train = np.load(CACHE_FILE + 'q2_train.npy')
        labels_train = np.load(CACHE_FILE + 'train_label.npy')
        q1_dev = np.load(CACHE_FILE + 'q1_dev.npy')
        q2_dev = np.load(CACHE_FILE + 'q2_dev.npy')
        labels_dev = np.load(CACHE_FILE + 'dev_label.npy')
        q1_test = np.load(CACHE_FILE + 'q1_test.npy')
        q2_test = np.load(CACHE_FILE + 'q2_test.npy')
        labels_test = np.load(CACHE_FILE + 'test_label.npy')
        word_index = np.load(CACHE_FILE + 'word_index.npy').item()
        embedding = load_embedding_matrix(word_index)
    else:
        q1_train, q2_train, labels_train = _load_x_y('./data/train.tsv')
        q1_test, q2_test, labels_test = _load_x_y('./data/test.tsv')
        q1_dev, q2_dev, labels_dev = _load_x_y('./data/dev.tsv')

        q1_train = _preprocess_texts(q1_train[:])
        q2_train = _preprocess_texts(q2_train[:])
        q1_test = _preprocess_texts(q1_test[:])
        q2_test = _preprocess_texts(q2_test[:])
        q1_dev = _preprocess_texts(q1_dev[:])
        q2_dev = _preprocess_texts(q2_dev[:])

        tokenizer = keras.preprocessing.text.Tokenizer(lower=False, filters='')

        tokenizer.fit_on_texts(q1_train + q2_train + q1_test + q2_test + q1_dev + q2_dev)

        q1_train = tokenizer.texts_to_sequences(q1_train)
        q2_train = tokenizer.texts_to_sequences(q2_train)
        # max([len(q) for q in q1_train])

        q1_test = tokenizer.texts_to_sequences(q1_test)
        q2_test = tokenizer.texts_to_sequences(q2_test)

        q1_dev = tokenizer.texts_to_sequences(q1_dev)
        q2_dev = tokenizer.texts_to_sequences(q2_dev)

        q1_train = keras.preprocessing.sequence.pad_sequences(q1_train, maxlen=50)  # 50 is chosen arbitrary!!!
        q2_train = keras.preprocessing.sequence.pad_sequences(q2_train, maxlen=50)

        q1_test = keras.preprocessing.sequence.pad_sequences(q1_test, maxlen=50)
        q2_test = keras.preprocessing.sequence.pad_sequences(q2_test, maxlen=50)

        q1_dev = keras.preprocessing.sequence.pad_sequences(q1_dev, maxlen=50)
        q2_dev = keras.preprocessing.sequence.pad_sequences(q2_dev, maxlen=50)

        np.save(CACHE_FILE + 'q1_train.npy', q1_train)
        np.save(CACHE_FILE + 'q2_train.npy', q2_train)
        np.save(CACHE_FILE + 'train_label.npy', labels_train)
        np.save(CACHE_FILE + 'q1_dev.npy', q1_dev)
        np.save(CACHE_FILE + 'q2_dev.npy', q2_dev)
        np.save(CACHE_FILE + 'dev_label.npy', labels_dev)
        np.save(CACHE_FILE + 'q1_test.npy', q1_test)
        np.save(CACHE_FILE + 'q2_test.npy', q2_test)
        np.save(CACHE_FILE + 'test_label.npy', labels_test)
        np.save(CACHE_FILE + 'word_index.npy', tokenizer.word_index)

        word_index = tokenizer.word_index
        embedding = load_embedding_matrix(word_index)

    return embedding, word_index, (q1_train, q2_train, labels_train), (q1_test, q2_test, labels_test), (
        q1_dev, q2_dev, labels_dev)
