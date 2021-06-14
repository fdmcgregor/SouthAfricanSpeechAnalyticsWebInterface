import os
import io
import re
import heapq
import pandas as pd
import operator
import matplotlib.pyplot as plt
import urllib
import base64
import datetime
from gensim.models import Word2Vec
from wordcloud import WordCloud, STOPWORDS
from django.core.files import File

def normalize_text(text):
    words = re.split('[!?., ]', text)
    words = [w.strip().lower() for w in words if len(w.strip()) > 0]
    return ' '.join(words)

def get_similar_words(input_word, lang):

    # select language
    if lang == 'eng':
        model_name = 'eng'
    elif lang == 'afr':
        model_name = 'afr'
    elif lang == 'zul':
        model_name = 'zulu'
    elif lang == 'stu':
        model_name = 'sotho'
    else:
        # default (multi) can just use english
        # model_name = 'eng'

        # Check if it occurs in any of the vocabularies first, load all models, store results for all languages that contain
        multi_results = {}
        for m in ['eng', 'afr', 'zulu', 'sotho']:

            model_path = f'models/{m}_model.bin'
            model = Word2Vec.load(model_path)

            if (model.wv.vocab.get(input_word) != None):
                print(f"word in {m}")
                related_words = model.wv.most_similar(positive=[input_word], topn=5)
                new = {k: v for k, v in zip([i[0] for i in related_words], [i[1] for i in related_words])}
                multi_results.update(new)

        # take the highest ranked
        result = heapq.nlargest(5, multi_results, key=multi_results.get)

        return result


    model_path = f'models/{model_name}_model.bin'

    # could potentially save this in cache
    model = Word2Vec.load(model_path)
    dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{dt}: Word2vec model loaded: {model}")

    if (model.wv.vocab.get(input_word) == None):
        print("Word not in the vocabulary")
        return ['']
    else:
        related_words = model.wv.most_similar(positive=[input_word], topn=5)
        result = [i[0] for i in related_words]

        return result

def search_transcript(target, text, words_json, n):

    text = normalize_text(text)

    text = text.split()

    indices = (i for i, word in enumerate(text) if word.lower() == target.lower())
    neighbors = []
    kw_indices = []
    for ind in indices:
        neighbors.append([' '.join(text[max(ind - n, 0):ind]), ' '.join(text[ind + 1:min(ind + n + 1, len(text))])])
        kw_indices.append(ind)


    # add timing info
    word_stats_l = []
    word_stats_r = []
    word_stats_c = []

    for i in kw_indices:

        # get keyword stats
        word_stats_c.append(words_json[i])

        # get left keyword stats
        kw_context_stats_l = []
        for j in range(max(i-n, 0), i):
            kw_context_stats_l.append(words_json[j])
        word_stats_l.append(kw_context_stats_l)

        # get right keyword stats
        kw_context_stats_r = []
        for j in range(i+1, min(i+n+1, len(words_json))):
            kw_context_stats_r.append(words_json[j])
        word_stats_r.append(kw_context_stats_r)

    return word_stats_c, word_stats_l, word_stats_r


# helper funcitons for search transcript sequence
def find_all(full_string, sub_string):
    start = 0
    while True:
        start = full_string.find(sub_string, start)
        if start == -1: return
        yield start
        start += len(sub_string)


def search_transcript_sequence(target, text, words_json, n):

    text = normalize_text(text)
    words = text.split()
    n_words = len(target.split())

    char_indices = list(find_all(text, target))

    neighbors = []
    kw_indices = []
    for ind in char_indices:
        left_string = text[0:ind]
        left_words = left_string.split()
        kw_indices.append(len(left_words))

        right_string = text[(ind + len(target)):] # dont include the words that are part of the target sequence
        right_words = right_string.split()

        neighbors.append([' '.join(left_words[max(len(left_words) - n, 0):-1]),
                          ' '.join(right_words[0:min(n+n_words, len(right_words))])])

    # add timing info
    word_stats_l = []
    word_stats_r = []
    word_stats_c = []

    for i in kw_indices:

        # get keywords stats
        seq_word = {}
        seq_word['word'] = target
        seq_word['startTime'] = words_json[i]['startTime']
        seq_word['endTime'] = words_json[i+len(target.split())]['endTime']
        seq_word['confidence'] = sum(
            [words_json[k]['confidence'] for k in range(i, i+len(target.split()))]
        )
        word_stats_c.append(seq_word)

        # get left keyword stats
        kw_context_stats_l = []
        for j in range(max(i-n, 0), i):
            kw_context_stats_l.append(words_json[j])
        word_stats_l.append(kw_context_stats_l)

        # get right keyword stats
        kw_context_stats_r = []
        for j in range(i+n_words, min(i+n+1+n_words, len(words_json))):
            kw_context_stats_r.append(words_json[j])
        word_stats_r.append(kw_context_stats_r)

    return word_stats_c, word_stats_l, word_stats_r

def search_across_files(word, user):

    # get model
    Post = apps.get_model(app_label='decoding_app', model_name='Post')
    results = Post.objects.filter(author=user).filter(transcription__icontains=word).order_by('-date_posted')

    # get number of hits in each file
    res_counts = []
    for res in results:
        # make sure it is a full word
        count = len(re.findall(r'\b'+ word + r'\b', res.transcription))
        if count > 0:
            res_counts.append([res, count])


    # sort by most hits
    res_counts = sorted(res_counts, key=operator.itemgetter(1), reverse=True)
    return res_counts

def create_wordcloud(input_text, lang):

    input_text = normalize_text(input_text)

    if lang == 'eng':
        stopwords=set(STOPWORDS)
        stopwords.update(['so', 'to'])
    elif lang == 'afr':
        stopwords=set(["en", "is", "die"])
    else:
        # dont have stopwords for non-english
        stopwords=set([])

    wc = WordCloud(background_color="white", max_words=200, width=400, height=400, random_state=42,
                       stopwords=stopwords).generate(input_text)

    plt.imshow(wc, interpolation='bilinear')
    plt.axis("off")

    image = io.BytesIO()
    plt.tight_layout(pad=0)
    plt.savefig(image, format='png')
    image.seek(0)  # rewind the data
    string = base64.b64encode(image.read())

    image_64 = 'data:image/png;base64,' + urllib.parse.quote(string)
    return image_64


from django.db.models import Sum
import datetime
from django.apps import apps


def get_account_info(user):

    # get model
    Post = apps.get_model(app_label='decoding_app', model_name='Post')

    # overall
    #'numfiles': Post.objects.filter(author=user).count(),
    #'numseconds': user.profile.total_seconds,
    #'amount': user.profile.total_amount

    # this month
    today = datetime.datetime.now()
    num_files = Post.objects.filter(author=user).filter(date_posted__year=today.year, date_posted__month=today.month).count()
    num_seconds = Post.objects.filter(author=user).filter(date_posted__year=today.year, date_posted__month=today.month).aggregate(Sum('audio_length'))['audio_length__sum']

    return num_files, num_seconds


import subprocess
import os
import uuid
import re

def check_file_and_get_length(f):

    '''
    Writes file to disk and checks if the file is and audio file which returns
    media=1 or accepted text file which returns media=1
    '''

    # Save the file to disk
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(BASE_DIR, 'tmp')
    if not os.path.exists(file_path):
        os.makedirs(file_path)

    file_name = os.path.join(file_path, f'{str(uuid.uuid4().hex)}.tmp')

    with open(file_name, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

    # check if media file and get file length with bash script
    cmd = f'bash {BASE_DIR}/decoding_app/extract_wav_from_other.sh {file_name} {file_path}/tmp'
    output = subprocess.run(cmd, shell=True)

    # get result written to <file_name>.txt
    res = open(f'{file_name}.txt', 'r', encoding='utf-8').readlines()
    media, duration = int(res[0].strip()), int(float(res[1].strip()))

    if media == 0:
        # check if it is accepted text file
        import mimetypes
        accepted_text_formats = ['text/plain', '.doc', '.docx', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
        if mimetypes.guess_type(f'{file_name}.txt')[0] in accepted_text_formats:
            media = 2

    # get num channels
    out, err = subprocess.Popen(['ffprobe', file_name, '-show_entries', 'stream=channels', '-select_streams', 'a', '-of', 'compact=p=0:nk=1', '-v', '0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    num_channels = int(out) if int(out) == 2 else 1

    # cleanup
    os.remove(f'{file_name}.txt')    
    os.remove(file_name)
    return media, duration, num_channels



def json_to_diarized_txt(words_json):

    current_speaker = words_json[0]['speaker']
    words_spoken = ''
    turns = []

    # extract words associated with each speaker turn
    for w in words_json:

        speaker = w['speaker']
        word = w['word']

        if speaker != current_speaker:
            # write turn
            turns.append(f'Speaker {current_speaker}: {words_spoken}')
            current_speaker = speaker
            words_spoken = word

        else:
            if len(words_spoken) > 0:
                words_spoken = words_spoken + ' ' + word
            else:
                words_spoken = word

    turns.append(f'Speaker {speaker}: {words_spoken}')

    # write speaker turns to file
    conversation_text = '\n'.join(turns)

    return conversation_text

def json_to_diarized_txt_list(words_json):

    current_speaker = words_json[0]['speaker']
    words_spoken = ''
    turns = []

    # extract words associated with each speaker turn
    for w in words_json:

        speaker = w['speaker']
        word = w['word']

        if speaker != current_speaker:
            # write turn
            turns.append(f'Speaker {current_speaker}: {words_spoken}')
            current_speaker = speaker
            words_spoken = word

        else:
            if len(words_spoken) > 0:
                words_spoken = words_spoken + ' ' + word
            else:
                words_spoken = word

    turns.append(f'Speaker {speaker}: {words_spoken}')

    return turns
