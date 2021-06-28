import spacy
from spacy import displacy
from sklearn import svm
from googletrans import Translator
import itertools
#感情分析のツール
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import MeCab

m = MeCab.Tagger ()
nltk.download('vader_lexicon')
nlp = spacy.load('ja_ginza')
tr = Translator(service_urls=['translate.googleapis.com'])
vader_analyzer = SentimentIntensityAnalyzer()

#文章から登場人物、関係を自動抽出する
def character_auto(txt):
    characters = set()
    parse = m.parse (txt)
    word_list = []
    for i in parse.split('\n'):
        bunseki = i.split('\t')
        if len(bunseki)>=2:
            if bunseki[1].split(',')[0] == '名詞':
                word_list.append(bunseki[0])
    
    doc = nlp(txt)
    ginza_only_set=set()

    
    for ent in doc.ents:
        if (ent.label_ in ['Person']) and (not('\u3000' in ent.text)) and (ent.text in word_list):
            characters.add(ent.text)
    return list(characters)

#txtの感情を分析する
def emotion_calculate(txt):
    trans = tr.translate(txt)
    result = vader_analyzer.polarity_scores(trans.text)
    emotions = [result['neg'], result['neu'], result['pos']]
    emotion = 2*emotions.index(max(emotions))+1
    return emotion
    

#txtから関係を抽出する
def relation_auto(txt, peoples):
    relation_list = []
    peoples_couple = itertools.combinations(peoples, 2)
    new = {}
    lines = txt.split('。')
    for i in lines:
        for j,k in itertools.combinations(peoples, 2):
            if (j in i) and (k in i):
                emotion = emotion_calculate(i)
                new_relation = {'source':j, 'target':k, 'relation':i, 'emotion':emotion}
                relation_list.append(new_relation)
    return relation_list

#新しく見つかった人物を追加する
def add_newpeople(peoples, new_peoples, peoples_info, line):
    for people in new_peoples:
         if not people in peoples:
             peoples.append(people)
             peoples_info.append({'people':people, 'line':line})
    return peoples, peoples_info

#新しく見つかった関係を追加する
def add_relation(relations_info, new_relations, line):
    
    for relation in new_relations:
        source = relation['source']
        target = relation['target']
        relationship = relation['relation']
        emotion = relation['emotion'] 
        relations_info.append({'source':source, 'target':target, 'relation':relationship, 'emotion':emotion, 'line':line})
    return relations_info

def auto_all(textline, people_list, relations_list):
    #すでに入力済みの人の集合
    already_peoples = [i['people'] for i in people_list]
    #updateされた人の集合
    peoples = [i for i in already_peoples]
    #新しい人と、その人の追加された場所の辞書
    peoples_info = people_list
    relations_info = relations_list
    for i in range(len(textline)):
        txt = textline[i]
        txt.replace('</p>', '')
        txt.replace('<p class = "info">', '')
        new_peoples = character_auto(txt)
        peoples, peoples_info = add_newpeople(peoples, new_peoples, peoples_info, i)
        new_relations = relation_auto(txt, peoples)
        relations_info = add_relation(relations_info, new_relations, i)
    return peoples_info, relations_info
         