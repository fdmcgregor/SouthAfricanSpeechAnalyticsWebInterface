import json
from django.shortcuts import render
from django.http import JsonResponse

from search.documents import PostDocument

from elasticsearch_dsl import Q


def get_rules(q, condition):
    
    ''' recursively parse query '''
    
    queries = []
    
    # (1) get list of queries
    # ----------------------------
    for rule in q['rules']:
        if 'condition' in rule:
            queries.append(get_rules(rule, rule['condition']))
        else:
            if rule['field'] == 'name':
                if rule['operator'] == 'contains':
                    queries.append(Q('wildcard', title=f"*{rule['value']}*"))
                elif rule['operator'] == 'not_contains':
                    queries.append(~Q('wildcard', title=f"*{rule['value']}*"))
            else:
                
                if rule['operator'] == 'contains fuzzy':
                    #queries.append(Q('fuzzy', transcription=rule['value'].lower()))
                    queries.append(Q('match', transcription={"query":rule['value'], "fuzziness": 4}))
                elif rule['operator'] == 'contains':
                    queries.append(Q('match', transcription=rule['value'].lower()))
                elif rule['operator'] == 'not_contains':
                    queries.append(~Q('match', transcription=rule['value'].lower()))
            
    # (2) return DSL version of query
    # ----------------------------
    
    QUERY = queries[0]
    
    if len(queries) > 1:
        for q_ in queries[1:]:
            if condition == "AND":
                QUERY = QUERY & q_
            else:   
                QUERY = QUERY | q_

    return QUERY

from django.contrib.auth.decorators import login_required
from decoding_app.models import Post

@login_required
def esearch(request): 
    
    if request.method == 'POST':
        
        q = json.loads(request.POST['search_query'])

        e_query = get_rules(q, q['condition'])

        # AND belongs to the user
        e_query =  e_query & Q('match', author__username=str(request.user))

        
        # parse queries
        posts = PostDocument.search().query(e_query).sort('_score')
        for hit in posts:
            print(f"HIT : {hit.title}, description {hit.date_posted}")

        posts = posts.to_queryset().filter(author=request.user)
        
        hits = []
        for hit in posts:
            print(f"HIT : {hit.title}, description {hit.date_posted}")
            hits.append(f"name : {hit.title}, posted: {hit.date_posted} transription {hit.transcription}")
        
        context = {"posts":posts, "hits":hits}
        return render(request, 'search/esearch_results.html', context)
    
    context = {'num_posts': Post.objects.filter(author=request.user).count()}

    return render(request, 'search/esearch.html', context)

