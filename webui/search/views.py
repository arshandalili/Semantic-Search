import torch
import faiss
import numpy as np
import pandas as pd
from pathlib import Path
from drf_yasg import openapi
from .models import CorpusEntry
from django.db.models import Q
from django.db.models import F
from faiss import write_index, read_index
from rest_framework import viewsets
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from .serializers import CorpusEntrySerializer
from sentence_transformers import SentenceTransformer, util

MODEL = None
INDEX = None
INDEX_PATH = 'search/data/index.faiss'

class CorpusEntryViewSet(viewsets.ViewSet):
    serializer_class = CorpusEntrySerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name='q',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description='The query string to search for.'
            ),
            openapi.Parameter(
                name='k',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description='The number of results to return.'
            )
        ],
    )
    @action(detail=True, methods=['get'])
    def semantic_search(self, request):
        global MODEL
        query = request.query_params.get('q', '')
        k = request.query_params.get('k', 5)
        query_embedding = MODEL.encode([query]).astype('float32')
        D, I = INDEX.search(query_embedding, int(k))
        queryset = CorpusEntry.objects.filter(Q(index__in=I[0]))
        serializer = CorpusEntrySerializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name='q',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description='The query string to add as a new entry.'
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def add_new_entry(self, request):
        query = request.query_params.get('q', '')
        query_embedding = MODEL.encode([query]).astype('float32')
        INDEX.add(query_embedding)
        new_entry = CorpusEntry.objects.create(index=INDEX.ntotal, text=query)
        new_entry.save()
        serializer = CorpusEntrySerializer(new_entry)
        sync_index()
        print('New entry successfully added to corpus!')
        return Response(serializer.data)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name='id',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description='The index of the entry to delete.'
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def delete_entry(self, request):
        index = request.query_params.get('id', '')
        INDEX.remove_ids(np.array([int(index)]))
        # decrement index of all entries with index > index
        CorpusEntry.objects.filter(index=int(index)).delete()
        CorpusEntry.objects.filter(index__gt=int(index)).update(index=F('index') - 1)
        sync_index()
        return Response({'message': f'Entry with index {index} deleted successfully.'})


def init_models():
    global MODEL, INDEX
    
    MODEL = SentenceTransformer('sentence-transformers/LaBSE') #  sentence-transformers/all-MiniLM-L6-v2 sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
    
    if Path(INDEX_PATH).is_file():
        print('Loading existing index...')
        INDEX = read_index(INDEX_PATH)
    else :
        print('Creating new index...')
        CORPUS = pd.read_csv('search/data/test.csv')
        CORPUS_EMBEDDING = MODEL.encode(CORPUS['Original Sentence'].to_list()).astype('float32')
        for i in range(len(CORPUS)):
            new_entry = CorpusEntry.objects.create(index=i, text=CORPUS['Original Sentence'][i])
            new_entry.save()
        
        INDEX = faiss.IndexFlatIP(CORPUS_EMBEDDING.shape[1])
        INDEX.add(CORPUS_EMBEDDING)
        write_index(INDEX, INDEX_PATH)
    
def sync_index():
    global INDEX
    write_index(INDEX, INDEX_PATH)


def home(request):
    init_models()
    return render(request, 'search/home.html')