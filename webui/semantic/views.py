import os
import csv
import torch
import zipfile
import pandas as pd
from django.apps import apps
from django.urls import reverse
from unicodedata import category
from django.db import connection
from django.db.models import Field
from matplotlib.style import context
from django.shortcuts import redirect, render
from django.core.exceptions import FieldError
from sklearn.linear_model import LogisticRegression
from django.http import HttpResponse, HttpResponseRedirect
from sentence_transformers import SentenceTransformer, util


REQUEST_K_KEY = 'k'
REQUEST_QUERY_KEY = 'query'
BUTTON_SEARCH_KEY = 'search'
BUTTON_ADD_KEY = 'add'
CHECK_EXPANSION_KEY = 'queryexpansion'

INITIALIZED = False
MODEL = None
CORPUS = None
CORPUS_EMBEDDING = None

def read_dataset_from_file():
    dataset = []
    with zipfile.ZipFile('semantic/models/dataset.zip', 'r') as zip_file:
        zip_file.extractall()
    with open('dataset.csv', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        header = next(csv_reader)
        for row in csv_reader:
            data = dict(zip(header[1:], row[1:]))
            dataset.append(data)
    os.remove('dataset.csv')
    return pd.DataFrame(dataset)


def data_to_text(data):
    return ' '.join([data['title'], data['intro'], data['body']]).lower()


def init_models():
    global CORPUS, CORPUS_EMBEDDING, MODEL
    
    # Load model
    MODEL = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2') # sentence-transformers/all-MiniLM-L6-v2

    # Load dataset and mini-datasets
    CORPUS = pd.read_csv('semantic/data/test.csv')
    CORPUS_EMBEDDING = MODEL.encode(CORPUS['Original Sentence'].to_list(), convert_to_tensor=True)


def home(request):
    global INITIALIZED
    if not INITIALIZED:
        init_models()
        INITIALIZED = True
    context = {
        'header': [],
        'header_title': [],
        'data': [],
    }
    if request.method == 'POST':
        if BUTTON_SEARCH_KEY in request.POST:
            search(request, context)
        elif BUTTON_ADD_KEY in request.POST:
            add(request, context)
    return render(request, 'semantic/home.html', context)


def search(request, context):
    query = request.POST.get(REQUEST_QUERY_KEY, None)
    k = int(request.POST.get(REQUEST_K_KEY, None))
    context['header_title'] = ['متن']
    context['header'] = ['body']
    query_embedding = MODEL.encode([query], convert_to_tensor=True)[0]
    search_result = util.semantic_search(query_embedding, CORPUS_EMBEDDING, top_k=k)[0]
    result = []
    for res in search_result:
        result.append({'body':CORPUS.iloc[res['corpus_id']]['Original Sentence']})
    context['data'] = result

def add(request, context):
    global CORPUS, CORPUS_EMBEDDING
    query = request.POST.get(REQUEST_QUERY_KEY, None)
    query_embedding = MODEL.encode([query], convert_to_tensor=True)
    temp_df = {'Original Sentence': query, 'Similar Sentence': ''}
    CORPUS = CORPUS.append(temp_df, ignore_index=True)
    CORPUS_EMBEDDING = torch.cat((CORPUS_EMBEDDING, query_embedding), 0)
