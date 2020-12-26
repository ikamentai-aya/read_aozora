
import re
import zipfile
import urllib.request
import os.path,glob
import pickle
import shutil
import math

import numpy as np
from bokeh.models import Paragraph,TextInput, PreText, Button, Slider, Dropdown, Select, Div, HoverTool, TapTool, BoxSelectTool, LinearColorMapper, BasicTicker, PrintfTickFormatter, ColorBar, CheckboxButtonGroup, Rect, CheckboxGroup, DataTable, TableColumn, GlyphRenderer, Spinner
from bokeh.plotting import figure, output_file, show, curdoc
from bokeh.models import ColumnDataSource
from bokeh.layouts import Column, Row
from bokeh import events
from class1 import Important
from modules.node import node_link, node_source, edge_source, source, provider
from modules.matrix import hm

from graphviz import Digraph #有向グラフ
from xml.dom import minidom

import sys
import spacy
from spacy import displacy
nlp = spacy.load('ja_ginza')



#それに対応する読書情報(class Important)を格納する辞書

#本ごとの読書情報を格納するクラス

#今読んでいる本の情報をいれる
important = Important('','',[],[],800,0,[],[],[],'', dict())
gr_path = 'dokusyo-aozora/data/graph_data/'
ch_frequency_dict = dict()
people_candidate = []


#実際に読書をする部分の設定

p = Div(text='',width=600, height=900) #本文
title = Div(text='', width =600, height = 15) #本のタイトル表示
author = Div(text='', width =600, height = 50) #本の作者表示

#読む本を選ぶためのwidget
import_down = Dropdown(label="小説の選択", button_type="warning", menu=['ダウンロード済み', '新たにダウンロード'], width=200)
already_import = Select(title="小説", value="none", options=['none'], width=200)
text_input= TextInput(value="default",title="URLを入力してください:", width=200) #新たにダウンロードする本のURLを打ち込むTextInput
finish_text = PreText(text='', width=100, height=20)

#新たに読む本を選ぶためのボタン、ダウンロード済みから選ぶor新たにダウンロードするかの選択
def import_renderer(event):
    curdoc().clear()
    if event.item == 'ダウンロード済み':
        lay_novel = Column(import_down, already_import)
    else:
        lay_novel = Column(import_down, text_input)
    
    menu = Row(lay1,lay2, bookmark, jump_mark,  input_info, lay_novel)
    reader = Column(title, author, p)
    lay = Column(menu, reader)

    curdoc().add_root(lay)
        
import_down.on_click(import_renderer)


#読む本を選択するための関数
def already_import_renderer(attr, old, new):
    if not (already_import.value == 'none'):

        #importantの書き換え
        new_title = already_import.value
        important.title = novel_dict[new_title].title
        important.author = novel_dict[new_title].author
        important.textline = novel_dict[new_title].textline
        important.pageNumber = novel_dict[new_title].pageNumber
        important.bookMark = novel_dict[new_title].bookMark
        important.people_list = novel_dict[new_title].people_list
        important.relation_list = novel_dict[new_title].relation_list
        important.row_text = novel_dict[new_title].row_text
        ch_frequency_dict = novel_dict[new_title].ch_freq

        title.text = "<style> .info{font-size:15px;} </style>"+'<p class = "info">'+important.title+"<p/>"
        author.text = '<p class = "info">'+important.author+"<p/>"
        
        page_slider.end = len(important.textline)
        page_slider.value = important.pageNumber
        
        #matrixの調整
        show_range_spinner.high = len(important.textline)
        show_range_spinner.value = len(important.textline)
        ch_now_list = []
        for i in important.people_list:
            if i['line'] <= page_slider.value:ch_now_list.append(i['people'])
        
        show_people_check.labels = ch_now_list
        show_people_check.active = list(range(len(ch_now_list)))
    
        #ブックマークの更新
        menu = []
        for i in novel_dict[important.title].bookMark:
            text = str(i)+' '
            for j in range(min([len(important.textline[i]), 30])):text += important.textline[i][j]
            text += '...'
            menu.append(text)
        
        jump_mark.menu = menu
        p.text = important.textline[important.pageNumber]
        save()

        if select_vis.value == '表示なし': 
            curdoc().clear()
            lay1 = Column(page_slider, select_vis)
            lay2 = Column(Row(forward_button, backward_button), auto_ch)
            menu = Row(lay1,lay2, bookmark, jump_mark, input_info, import_down)
            reader = Column(title, author, p)
            lay = Column(menu, reader)
            curdoc().add_root(lay)

        if select_vis.value == '関係図(◯-◯)':make_node_link()
        if select_vis.value == '関係図(⬜️)': make_matrix()
        if select_vis.value == '編集画面':make_table()
    
already_import.on_change('value', already_import_renderer)

#url_getのsub routin
def convert(download_text):
    if download_text == 0:
        return 0,0,0
    else:    
        binarydata = open(download_text, 'rb').read()
        text = binarydata.decode('shift_jis')
 
        # ルビ、注釈などの除去

        honbun = re.split(r'\-{5,}', text)[2]
        title_author = re.split(r'\-{5,}', text)[0]
        title = title_author.split('\n')[0]
        author = title_author.split('\n')[1]

        honbun = re.split(r'底本：', honbun)[0]
        honbun = re.sub(r'《.+?》', '', honbun)
        honbun = re.sub(r'［＃.+?］', '', honbun)
        honbun = re.sub(r'｜', '', honbun)
        honbun = honbun.strip()

        os.remove(download_text)
    
        return title, author, honbun

#url_getのsub　routin
def download(url):
    # データファイルをダウンロードする
    zip_file = 'dokusyo-aozora/data/aozora/' + re.split(r'/', url)[-1]
    
    urllib.request.urlretrieve(url, zip_file)
    print('ここまで完了')

    # フォルダの生成
    dir, ext = os.path.splitext(zip_file)
    if not os.path.exists(dir):
        os.makedirs(dir)

    print('ダウンロードOK')
 
    # zipファイルの展開
    zip_obj = zipfile.ZipFile(zip_file, 'r')
    zip_obj.extractall(dir)
    zip_obj.close()
 
    # zipファイルの削除
    os.remove(zip_file)

    # テキストファイルの抽出
    path = os.path.join(dir,'*.txt')
    list = glob.glob(path)
    new_path = list[0]

    #ファイルの移動
    paths = new_path.split('/')[-1]
    check_path = 'dokusyo-aozora/data/aozora/' + paths
    
    #if not os.path.exists(check_path):
    if not (check_path in already_novels):
        print('Download URL')
        print('URL:',url)
        shutil.move(new_path, 'dokusyo-aozora/data/aozora')
        shutil.rmtree(dir)
        return check_path
        
    else:
        print('Download File exists')
        shutil.rmtree(dir)
        return 0

#小説のURLを入力されたら、小説をダウンロードして、読めるように整形する関数
def url_get(attr, old, new):
    url = text_input.value
    download_text = download(url) #入っているファイルのパスを返す
    title, author, text = convert(download_text)
    if (title==0 and author == 0 and text == 0):
        finish_text.text = 'ダウンロード済みです'
    else: 
        
        lines = []
        row_lines = []
        style = ""
        for i in range(len(text)//800):
            mini_text = text[(800*i):(800*(i+1))]
            mini_lines = mini_text.split('\n')
            row_lines.append(mini_text)
            m_text = style
            for j in mini_lines: m_text += '<p class = "info">'+j+'</p>'
            lines.append(m_text)

        if not (len(text)%800 == 0):
            mini_text = text[(len(text)//800)*800:]
            mini_lines = mini_text.split('\n')
            row_lines.append(mini_text)
            m_text = style
            for j in mini_lines: m_text += '<p class = "info">'+j+'</p>'
            lines.append(m_text)
        
        g_path = gr_path + title
        os.mkdir(g_path)
        novel_dict[title] = Important(title, author, lines, row_lines,800, 0, [], [], [], g_path, dict())
        novel_list.append(title)
        already_import.options = novel_list
        save()
        finish_text.text = 'ダウンロードが完了しました'

    
    curdoc().clear()
    lay_novel = Column(import_down, text_input, finish_text)

    menu = Row(lay1,lay2,bookmark, jump_mark, input_info, lay_novel)
    #reader = Column(title, author, p)
    lay = Column(menu, reader)

    curdoc().add_root(lay)


text_input.on_change('value', url_get)


#ページをスクロールするボタン

def forward_renderer():
    head = important.pageNumber + 1
    if head <= page_slider.end:
        page_slider.value = head


def backward_renderer():
    head = important.pageNumber -1
    if head >= 0:
        page_slider.value = head
 
    
    
forward_button = Button(label='▷', button_type='success', width=100)
backward_button = Button(label='◁', button_type='success', width=100)

forward_button.on_click(forward_renderer)
backward_button.on_click(backward_renderer)

#sliderの実装

def page_slider_renderer(attr, new, old):

    head = page_slider.value
    important.pageNumber = head
    novel_dict[important.title].pageNumber = head
    p.text = important.textline[head]

    if select_vis.value == '関係図(◯-◯)':make_node_link()
    if select_vis.value == '関係図(⬜️)': make_matrix()
    if select_vis.value == '編集画面': 
        person = [ch_source.data['people'][i] for i in ch_source.selected.indices]
        novel_coloring(person, 'yellow')

    
    save()

page_slider = Slider(start=0, end=len(important.textline)+1, value=1, step=1, title="現在の段落", width=200)
page_slider.on_change('value', page_slider_renderer)

#しおりに飛ぶ
jump_mark = Dropdown(label="しおりに飛ぶ", button_type="warning", menu=[], width = 200)
def jump_renderer(event):
    spl = event.item.split(' ')
    head = int(spl[0])
    page_slider.value = head
    
jump_mark.on_click(jump_renderer)


#しおりの追加
bookmark = Button(label='しおり', button_type='success', width=100)
def book_renderer():
    if (page_slider.value in important.bookMark) == False:
        novel_dict[important.title].bookMark.append(page_slider.value)
        important.bookMark = novel_dict[important.title].bookMark

        menu = []
        for i in novel_dict[important.title].bookMark:
            text = str(i)+' '
            print(len(important.row_text), len(important.textline))
            for j in range(min([len(important.row_text[i]), 30])):text += important.row_text[i][j]
            text += '...'
            menu.append(text)

        
        jump_mark.menu = menu
        save()

    
bookmark.on_click(book_renderer)

#関係を入力するフォーム

input_info = Dropdown(label="情報追加", button_type="warning", menu=['登場人物追加', '関係性追加', '人物情報追加'], width=200)

chracter_input = TextInput(value="default",title="人物を入力してください", width = 200)
decide_ch = Button(label='以上の人物を追加', button_type='success', width = 200)

#入力された情報を新しく登場人物としてデータに保存
def chracter_renderer():
    
    ch_list = []
    for i in novel_dict[important.title].people_list:
        ch_list.append(i['people'])
    if not (chracter_input.value in ch_list):
        novel_dict[important.title].people_list.append({'people':chracter_input.value, 'line':page_slider.value})
        important.people_list=novel_dict[important.title].people_list 
        save()
        if select_vis.value == '関係図(◯-◯)':make_node_link()
        if select_vis.value == '関係図(⬜️)': make_matrix()

decide_ch.on_click(chracter_renderer)

#入力された情報を新しく関係性としてデータに保存
def relation_renderer():
    
    new_dict = {'source':source_input.value, 'target':target_input.value, 'line':page_slider.value, 'emotion':emotion_input.value, 'relation':relation_input.value}
    novel_dict[important.title].relation_list.append(new_dict)

    #novel_dict[important.title].relation_list.append({'source':source_input.value, 'target':target_input.value, 'line':important['headNumber'], 'emotion':emotion_input.value, 'relation':relation_input.value})
    important.relation_list = novel_dict[important.title].relation_list
    save()
    if select_vis.value == '関係図(◯-◯)':make_node_link()
    if select_vis.value == '関係図(⬜️)': make_matrix()

source_input = Select(title='誰から',value='none',options=['none'], width=200)
target_input = Select(title='誰への',value='none',options=['none'], width=200)
relation_input = TextInput(value='default',title='どんな関係', width=200)
emotion_input = Slider(start=1, end=5, value=1, step=1, title="好意的か（5:好意的、1:否定的）", width=200)
decide_button = Button(label='以上の関係を追加', button_type='success', width=200)
decide_button.on_click(relation_renderer)
    
#これから登場人物を追加するのか、関係性を追加するのか決定する
def input_renderer(event):
    curdoc().clear()

    if event.item == '登場人物追加':
        lay_input = Column(input_info, chracter_input, decide_ch)
    
    if event.item == '関係性追加':
        people = ['none']
        for i in important.people_list:
            if i['line'] <= page_slider.value:people.append(i['people'])
        source_input.options=people
        target_input.options=people
        lay_input = Column(input_info, source_input, target_input, relation_input, emotion_input, decide_button)

    menu = Row(lay1,lay2,bookmark, jump_mark, lay_input, import_down)
    reader = Column(title, author, p)
    lay = Column(menu, reader)
    curdoc().add_root(lay) 
    save()       
    
input_info.on_click(input_renderer)

#必要な情報を保存する
def save():
    with open('dokusyo-aozora/data/novel_dict.binaryfile', 'wb') as sp:
        pickle.dump([novel_dict,novel_list, already_novels] , sp)



####可視化の選択など####
select_vis = Select(title="可視化の選択", value="表示なし", options=['表示なし', '関係図(◯-◯)', '関係図(⬜️)','編集画面'], width=200)

def select_vis_renderer(attr, old, new):
    
    if select_vis.value == '関係図(◯-◯)':
        curdoc().clear()
        u_lay = Row(reader, node_link)
        make_node_link()
        lay = Column(menu, u_lay)
        curdoc().add_root(lay)

    elif select_vis.value == '関係図(⬜️)':
        make_matrix()

    elif select_vis.value == '編集画面':
        make_table()
    else:
        curdoc().clear()
        u_lay = reader
        lay = Column(menu, u_lay)
        curdoc().add_root(lay)


select_vis.on_change('value',select_vis_renderer)

#ノードリンク図を作成する関数
def make_node_link():
    p.text = important.textline[page_slider.value]
    save_path = make_graphvis(page_slider.value)
    import_graph_info(save_path)
    
#情報をgraphvisに入れてグラフを作成する
def make_graphvis(line_number):

    graph = Digraph(format='svg',
                    graph_attr={'size':"600,600"})
 

    graph.engine= 'sfdp'

    ch_list = important.people_list
    new_ch_list = [] #現在までに出てきている人のリスト
    for i in ch_list:
        if i['line'] <= line_number:
            new_ch_list.append(i['people'])
            #graph.node(i['people'])

    new_ch_size = dict()
    for i in new_ch_list:new_ch_size[i] = 100


    re_list = important.relation_list
    new_re_dict = dict()
    for j in re_list:
        if j['line'] <= line_number:
            new_re_dict[j['source']+','+j['target']] = j['relation']
            new_ch_size[j['source']] += 10
            new_ch_size[j['target']] += 10
    
    for i in new_ch_list:
        graph.attr('node', fixedsize='true', width=str(new_ch_size[i]*3), height = str(new_ch_size[i]))
        graph.node(i)


    for j in new_re_dict:
        j_list = j.split(',')
        graph.edge(j_list[0],j_list[1],new_re_dict[j])

    save_path = novel_dict[important.title].graph_path +'/'+ str(line_number)

    graph.render(save_path)
    return save_path

#save_pathに保存されたグラフから情報を取得する
def import_graph_info(save_path):

    line_number = page_slider.value

    relation_list = important.relation_list
    #re_emo_dict = [[], [], [], [], []]
    re_emo_dict = dict()
    for j in relation_list:
        if j['line'] <= line_number:
            #re_emo_dict[j['emotion']-1].append([j['source'], j['target']])
            re_emo_dict[j['source']+j['target']] = j['emotion']-1

    colors = ['#000000', '#003333', '#006666', '#009999', '#00CCCC']
 

    node_indices = [] #ノードのインデックス
    x_list = []; y_list = [] #ノードのx,y座標
    rx_list = []; ry_list = [] #ノードの縦横さいず
    color = [] #関係の色５段階
    starts = [] #関係のsource
    ends = [] #関係のtarget
    edge_index = [] #edgeのインデックス
    edge_color = [] #edgeの色
    edge_emotion = []

    doc = minidom.parse(save_path+'.svg')

    for g in doc.getElementsByTagName('g'):

        nodeclass = g.getAttribute('class')
        #classがnodeだった時
        if nodeclass == 'node':
            ids = g.getElementsByTagName('title')[0].childNodes[0].nodeValue
            x = g.getElementsByTagName('ellipse')[0].getAttribute('cx')
            y = g.getElementsByTagName('ellipse')[0].getAttribute('cy')
            rx = g.getElementsByTagName('ellipse')[0].getAttribute('rx')
            ry = g.getElementsByTagName('ellipse')[0].getAttribute('ry')
            if g.getElementsByTagName('ellipse')[0].getAttribute('fill')=='none':fill = 'white'
            else: fill = g.getElementsByTagName('ellipse')[0].getAttribute('fill')
            node_indices.append(ids)
            x_list.append(float(x)/10.0); y_list.append(float(y)/10.0)
            rx_list.append(float(rx)/5.0); ry_list.append(float(ry)/5.0)
            
            color.append(fill)
            
        #classがedgeだった時
        if nodeclass == 'edge':
            title = g.getElementsByTagName('title')[0].childNodes[0].nodeValue
            m = title.split('->')
            starts.append(m[0]);ends.append(m[1])
            e = g.getElementsByTagName('text')[0].childNodes[0].nodeValue
            edge_index.append(e)
            edge_color.append(colors[re_emo_dict[m[0]+m[1]]])
            edge_emotion.append(re_emo_dict[m[0]+m[1]]+1)
            
    #startからendへの曲線を生成する
    def bezier(start, end, control, steps, bias):
        bias = bias/5
        half = (steps[-1]-steps[0])/2
        max_bias = half ** 2
        ll = []
        bias_list = []
        for s in steps:
            now_bias =(half-s)**2
            now_bias = (max_bias - now_bias)*bias
            bias_list.append(now_bias)
            ll.append(start*(1-s)+end*s+now_bias)
        return ll
        
    steps = [i/100. for i in range(100)]
    e_xs, e_ys = [], []

    graph_layout = dict(zip(node_indices, zip(x_list, y_list))) #nodeのindexとx,y座標が対応する辞書
    steps = [i/100. for i in range(100)]
    for i, j in zip(starts, ends):
        sx, sy = graph_layout[i]
        ex, ey = graph_layout[j]
        if abs(sx-ex) > abs(sy-ey):
            e_xs.append(bezier(sx, ex, 0, steps, 0))
            e_ys.append(bezier(sy, ey, 0, steps, sx-ex))
        else:
            e_xs.append(bezier(sx, ex, 0, steps, sy-ey))
            e_ys.append(bezier(sy, ey, 0, steps, 0))

    
    t_xs = []
    t_ys = []
    for e_x, e_y in zip(e_xs, e_ys):
        p1_x = e_x[-40]; p1_y = e_y[-40]
        h_x = e_x[-50]; h_y = e_y[-50]
        d_x = p1_x-h_x; d_y = p1_y-h_y
        dph = (d_x**2 + d_y**2)//2
        d_x = d_x/2
        d_y = d_y/2
        p2_x = h_x +d_y; p2_y = h_y -d_x
        p3_x = h_x -d_y; p3_y = h_y +d_x
        t_xs.append([p1_x, p2_x, p3_x])
        t_ys.append([p1_y, p2_y, p3_y])
    

    node_source.data = dict(index = node_indices, color = color, rx = rx_list, ry = ry_list, chapter = [page_slider.value]*len(node_indices))

    if not (starts==[]):
        edge_source.data = dict(start = starts, end = ends, index = edge_index, color = edge_color, emotion = edge_emotion, xs = e_xs, ys=e_ys)
        #head_source.data = dict(xs=t_xs, ys=t_ys, color = edge_color, line_color = edge_color)

    provider.graph_layout = dict(zip(node_indices,zip(x_list,y_list)))
    x_axis = [i for i in x_list]
    
    source.data = dict(x=x_axis, y=y_list, text=node_indices)

    os.remove(save_path+'.svg')



show_range_spinner = Spinner(title="直近何ページの関係を表しますか", low=1, high=1, step=1, value=1, width=70)
show_main_people = Select(title="この人を中心とする", value="none", options=['none'], width=200)
show_people_check = CheckboxGroup(labels=[], active=[])

#マトリックス図を作成する関数
def make_matrix_sub(center, initial_set):
    #p.text = important.textline[page_slider.value]
    line_number = page_slider.value 

    ch_now_list = show_people_check.labels
    relation_list = important.relation_list
    if initial_set: show_people_check.active = list(range(len(ch_now_list)))

    re_now_list = []
    re_emotion_list = []
    start_line = max(page_slider.value - show_range_spinner.value, 0)#ここからの関係を写す

    

    
    if center == True:
        main_people = show_main_people.value
        if main_people == 'none':
            ch_show_list = []
            for i in important.people_list:
                if (i['line'] >= start_line) and (i['line'] <= page_slider.value):ch_show_list.append(i['people'])
            for j in relation_list:
                if j['line'] >= start_line: 
                    re_now_list.append([j['source'], j['target']])
                    re_emotion_list.append([j['emotion'],j['relation'],j['line']])
            show_people_check.active = list(range(len(ch_now_list)))
        else:
            for j in relation_list:
                if (j['line'] <= page_slider.value) and (j['line'] >= start_line) and ((j['source']==main_people)or(j['target']==main_people)): 
                    re_now_list.append([j['source'], j['target']])
                    re_emotion_list.append([j['emotion'],j['relation'],j['line']])
            ch_show_list = set()
            for j in re_now_list:
                ch_show_list.add(j[0])
                ch_show_list.add(j[1])
            ch_show_list = list(ch_show_list)
            ch_show_index = []
            for i in range(len(ch_now_list)):
                if ch_now_list[i] in ch_show_list:ch_show_index.append(i)
            show_people_check.active = ch_show_index
    else:
        ch_show_list=[]
        print(show_people_check.active)

        for i in show_people_check.active:
            if i < len(ch_now_list):
                ch_show_list.append(ch_now_list[i])
        for j in relation_list:
            if (j['line'] <= page_slider.value) and (j['line'] >= start_line) and ((j['source'] in ch_show_list)and(j['target'] in ch_now_list)): 
                re_now_list.append([j['source'], j['target']])
                re_emotion_list.append([j['emotion'],j['relation'],j['line']])
        
   
    colors = ['#000000', '#003333', '#006666', '#009999', '#00CCCC']
    
    x_mem = ch_show_list * len(ch_show_list)
    y_mem = []
    colors_list = []
    relation_indices = []
    for i in ch_show_list:y_mem += ([i]*len(ch_show_list))
    
    #color_listを作る
    for i, j in zip(y_mem, x_mem):
        if [i,j] in re_now_list:
            i_j_color='white'
            i_j_relation='none'
            for k in range(len(re_now_list)):
                if re_now_list[k] == [i,j]:
                    pair = re_emotion_list[k]
                    i_j_color=colors[int(pair[0])-1]
                    i_j_relation=pair[1]
            colors_list.append(i_j_color)
            relation_indices.append(i_j_relation)
        else:
            colors_list.append('white')
            relation_indices.append('none')

    
    hm_source = ColumnDataSource(data = dict(x = x_mem, y = y_mem, colors = colors_list, relation = relation_indices))
    toolList = ['pan', 'box_zoom', 'lasso_select', 'poly_select', 'tap', 'reset', 'save']
    hm = figure(title = '関係図(⬜️)', x_range = ch_show_list, y_range=ch_show_list, width = 600, height = 600, tools = toolList)
  
    hm.xaxis.axis_label = '誰への'
    hm.yaxis.axis_label = '誰から'
    
    
    hm.xaxis.major_label_orientation = math.pi/2
    heat_renderer = GlyphRenderer(data_source=hm_source)
    heat_renderer.glyph = Rect(x="x", y="y", width=1, height=1, fill_color="colors", line_color = 'black', line_alpha=0.3)
    #heat_renderer.selection_glyph = Rect(line_color='red')

    edge_hover_tool = HoverTool(tooltips=[("誰から","@y"),("誰への","@x"),("どんな関係","@relation")])
    hm.add_tools(edge_hover_tool)
    
    hm.renderers.append(heat_renderer)

    st_columns = [
        TableColumn(field="line", title="ページ", width=70),
        TableColumn(field="relation", title="関係性"),
        TableColumn(field='emotion', title='好感度', width=70)
    ]

    st_text = PreText(text='', width=100, height=20)

    def hmTap_callback():
        curdoc().clear()
        if len(hm_source.selected.indices)>0:
            select_Row=hm_source.selected.indices[0]
            source = hm_source.data['y'][select_Row]
            target = hm_source.data['x'][select_Row]

            if [source, target] in re_now_list:
                st_relation = []
                st_emotion = []
                st_lines = []

                for k in range(len(re_now_list)):
                    if re_now_list[k] == [source,target]:
                        pair = re_emotion_list[k]
                        st_emotion.append(int(pair[0]))
                        st_relation.append(pair[1])
                        st_lines.append(pair[2])

                st_source=ColumnDataSource(dict(line=st_lines, relation=st_relation, emotion=st_emotion))
                st_table = DataTable(source=st_source, columns=st_columns, width=600, height=250, editable = True, scroll_to_selection = True, selectable =True)
                
                def st_table_renderer(attr, old, new):
                    if len(st_source.selected.indices) >0:
                        st_select_row = st_source.selected.indices[0]
                        page_slider.value = st_source.data['line'][st_select_row]

                st_source.selected.on_change('indices', st_table_renderer)

                st_text.text = source + 'から'+target+'への関係一覧'

                curdoc().clear()
                u_lay = Row(reader, Column(hm, st_text,st_table),Column(show_range_spinner, show_main_people, show_people_check))
                lay = Column(menu, u_lay)
                curdoc().add_root(lay)

            else:
                curdoc().clear()
                u_lay = Row(reader, hm, Column(show_range_spinner, show_main_people, show_people_check))

                lay = Column(menu, u_lay)
                curdoc().add_root(lay)
        else:
            curdoc().clear()
            u_lay = Row(reader, hm, Column(show_range_spinner, show_main_people, show_people_check))
            lay = Column(menu, u_lay)
            curdoc().add_root(lay)

    hm.on_event(events.Tap, hmTap_callback)

    curdoc().clear()
    u_lay = Row(reader, hm, Column(show_range_spinner, show_main_people, show_people_check))

    lay = Column(menu, u_lay)
    curdoc().add_root(lay)

def show_main_renderer(attr, old, new):
    make_matrix_sub(True, False)

def show_people_renderer(attr, old, new):
    make_matrix_sub(False, False)

def show_range_renderer(attr, old, new):
    if not(show_range_spinner.value == len(important.textline)):make_matrix_sub(False, False)

show_main_people.on_change('value', show_main_renderer)
show_people_check.on_change('active', show_people_renderer)
show_range_spinner.on_change('value', show_range_renderer)


#マトリックス図を選択されたときに表示する関数
def make_matrix():

    curdoc().clear()
    initial_set = False

    #if show_range_spinner.high == 1: initial_set = True 
    show_range_spinner.high = len(important.textline)
    
    ch_list = important.people_list
    ch_now_list = []
    
    for i in ch_list:
        if i['line'] <= page_slider.value: ch_now_list.append(i['people'])
    
    
    show_main_people.options = ['none']+ ch_now_list
    show_people_check.labels = ch_now_list 

    make_matrix_sub(False, initial_set)

    
#キャラクターを削除する関数
def ch_remove_renderer():
    selectionRow=ch_source.selected.indices
    for i in selectionRow:
        rm_people=ch_source.data['people'][i]
        rm_line=ch_source.data['line'][i]

        important.people_list.remove({'people':rm_people, 'line':rm_line})
        novel_dict[important.title].people_list=important.people_list
    save()
    make_table()

#関係性を削除する関数
def re_remove_renderer():
    selectionRow=re_source.selected.indices
    for i in selectionRow:
        rm_source=re_source.data['source'][i]
        rm_target=re_source.data['target'][i]
        rm_relation=re_source.data['relation'][i]
        rm_emotion=re_source.data['emotion'][i]
        rm_line=re_source.data['line'][i]

        important.relation_list.remove({'source':rm_source, 'target':rm_target, 'relation':rm_relation, 'emotion':rm_emotion, 'line':rm_line})
        novel_dict[important.title].relation_list=important.relation_list
    save()
    make_table()

#関係性の編集の保存
def ch_edit_renderer():
    people_list = important.people_list
    now_people = []
    for i in people_list:
        now_people.append(i['people'])
    new_people = []

    new_old_dict = dict()
    for i, j in zip(now_people, ch_source.data['people']): new_old_dict[i] = j

    for people, line in zip(ch_source.data['people'], ch_source.data['line']):
        new_people.append({'people':people, 'line':int(line)})
    
    novel_dict[important.title].people_list = new_people
    important.people_list = new_people

    new_relation_list = []
    for j in important.relation_list:
        j['source'] = new_old_dict[j['source']]
        j['target'] = new_old_dict[j['target']]
        new_relation_list.append(j)

    novel_dict[important.title].relation_list = new_relation_list
    important.relation_list = new_relation_list

    make_table()

    save()


#関係しの編集の保存
def re_edit_renderer():
    new_relation = []
    for source, target, relation, emotion, line in zip(re_source.data['source'], re_source.data['target'], re_source.data['relation'], re_source.data['emotion'], re_source.data['line']):
        emotion = int(emotion)
        line = int(line)
        new_relation.append({'source':source, 'target':target, 'relation':relation, 'emotion':emotion, 'line':line})

    novel_dict[important.title].relation_list = new_relation
    important.relation_list = new_relation
    save()

#登場人物表の追加
def ch_plus_renderer():
    peoples = ch_source.data['people']
    lines = ch_source.data['line']
    peoples.append('')
    lines.append('')
    ch_source.data = dict(people=peoples, line=lines)

#関係性表の追加
def re_plus_renderer():
    source = re_source.data['source']
    target = re_source.data['target']
    relation = re_source.data['relation']
    emotion = re_source.data['emotion']
    line = re_source.data['line']
    source.append('')
    target.append('')
    relation.append('')
    emotion.append('')
    line.append('')
    re_source.data = dict(source=source,target=target,relation=relation,emotion=emotion, line=line)

#登場人物表の行の削除
def ch_minus_renderer():
    peoples = ch_source.data['people']
    lines = ch_source.data['line']
    if ('' in peoples) or ('' in lines): 
        peoples.remove('')
        lines.remove('')
        ch_source.data = dict(people=peoples, line=lines)

#関係性表の行の削除
def re_minus_renderer():
    source = re_source.data['source']
    target = re_source.data['target']
    relation = re_source.data['relation']
    emotion = re_source.data['emotion']
    line = re_source.data['line']
    if ('' in source) or ('' in target ) or ('' in relation) or ('' in emotion) or ('' in line):
        source.remove('')
        target.remove('')
        relation.remove('')
        emotion.remove('')
        line.remove('')
        re_source.data = dict(source=source,target=target,relation=relation,emotion=emotion, line=line)


frequency_color = ['white', '#d5eaff', '#aad5ff', '55aaff', '#0080ff','#006ad5','#004080','#002b55']
frequency_count = [[0],[1,2],[3,4],[5,6],[7,8],[9,10],[11,12]]


def ch_select_renderer(attr, old, new):
    person = [ch_source.data['people'][i] for i in ch_source.selected.indices]
    novel_coloring(person, 'yellow')
    for i in person:
        if not (i in ch_frequency_dict):
            frequency = []
            for page in important.textline:
                frequency.append(page.count(i))
            ch_frequency_dict[i] = frequency
            print(ch_frequency_dict[i])

    x_range=[str(i) for i in range(len(important.textline))]
    height = len(person)*10
    toolList = ['pan', 'box_zoom', 'lasso_select', 'poly_select', 'tap', 'reset', 'save']
    frequency_heat = figure(plot_width=700, plot_height=200, x_range=x_range, y_range=person, tools=toolList)
    
    xs = list(range(len(important.textline))) * len(person)
    ys = []
    for i in person:ys += [i]*len(important.textline)
    color=[]
    fre_count = []

    for x, y in zip(xs, ys):
        fre_count.append(ch_frequency_dict[y][x])
        sude = False
        for i in range(7):
            if (ch_frequency_dict[y][x] in frequency_count[i]):
                color.append(frequency_color[i])
                sude = True
        if sude == False:color.append(frequency_color[7])
    
    fre_source = ColumnDataSource(data = dict(page = xs, person = ys, colors = color, count=fre_count))
    fre_renderer = GlyphRenderer(data_source=fre_source)
    fre_renderer.glyph = Rect(x="page", y="person", width=1, height=1, fill_color="colors", line_color='black', line_alpha=0.3)
    
    frequency_heat.renderers.append(fre_renderer)

    fre_hover_tool = HoverTool(tooltips=[("誰","@person"),("ページ","@page"),("出現回数","@count")])
    frequency_heat.add_tools(fre_hover_tool)

    
    def fre_heat_Tap():
        if len(fre_source.selected.indices) >0:
            page_slider.value=fre_source.data['page'][fre_source.selected.indices[0]]
            fre_source.selected.indices = []

    fre_taptool = frequency_heat.select(type=TapTool)
    frequency_heat.on_event(events.Tap, fre_heat_Tap)

    frequency_heat.on_event(events.Tap, fre_heat_Tap)

    curdoc().clear()
    edit_lay = Column(Row(ch_plus_button, ch_minus_button), Row(ch_table, Column(ch_delete_button, ch_edit_button)),frequency_heat,Row(re_plus_button, re_minus_button), Row(re_table, Column(re_delete_button, re_edit_button)))
    u_lay = Row(reader, edit_lay)
    lay = Column(menu, u_lay)
    curdoc().add_root(lay)

    novel_dict[important.title].ch_freq = ch_frequency_dict

    save()

ch_source=ColumnDataSource(data=dict(people=[], line=[]))

ch_columns = [
        TableColumn(field="people", title="人物名"),
        TableColumn(field="line", title="初登場ページ"),
    ]
ch_table = DataTable(source=ch_source, columns=ch_columns, width=600, height=250, editable = True, scroll_to_selection = True, selectable = 'checkbox')

re_source=ColumnDataSource(data=dict(source=[], target=[], relation=[], emotion = [], line=[]))
re_columns = [
    TableColumn(field="source", title="誰から"),
    TableColumn(field="target", title="誰への"),
    TableColumn(field="relation", title="関係"),
    TableColumn(field="emotion", title="好感度"),
    TableColumn(field="line", title="ページ")
]
re_table = DataTable(source=re_source, columns=re_columns, width=600, height=250, editable = True, scroll_to_selection = True, selectable =True)


ch_delete_button = Button(label='消去', button_type='success', width =100)
ch_delete_button.on_click(ch_remove_renderer)
ch_edit_button = Button(label='変更を保存', button_type='success', width=100)
ch_edit_button.on_click(ch_edit_renderer)
ch_plus_button = Button(label='+', button_type='success', width=50, background='white')
ch_plus_button.on_click(ch_plus_renderer)
ch_minus_button = Button(label='-', button_type='success', width=50, background='white')
ch_minus_button.on_click(ch_minus_renderer)
ch_source.selected.on_change('indices', ch_select_renderer)




re_delete_button = Button(label='消去', button_type='success', width =100)
re_delete_button.on_click(re_remove_renderer)
re_edit_button = Button(label='変更を保存', button_type='success', width=100)
re_edit_button.on_click(re_edit_renderer)
re_plus_button = Button(label='+', button_type='success', width=50, background='white')
re_plus_button.on_click(re_plus_renderer)
re_minus_button = Button(label='-', button_type='success', width=50, background='white')
re_minus_button.on_click(re_minus_renderer)



#編集のための表を作る関数
def make_table():
    
    print(important.people_list)
    ch_source.data = dict(
        people = [i['people'] for i in important.people_list],
        line=[i['line'] for i in important.people_list],
    )

    re_source.data = dict(
        source = [i['source'] for i in important.relation_list],
        target = [i['target'] for i in important.relation_list],
        relation = [i['relation'] for i in important.relation_list],
        emotion = [i['emotion'] for i in important.relation_list],
        line = [i['line'] for i in important.relation_list]
    )

    p.text = important.textline[important.pageNumber]
    curdoc().clear()
    ch_source.selected.indices = []
    person = [ch_source.data['people'][i] for i in ch_source.selected.indices]
    novel_coloring(person, 'yellow')
    edit_lay = Column(Row(ch_plus_button, ch_minus_button), Row(ch_table, Column(ch_delete_button, ch_edit_button)),Row(re_plus_button, re_minus_button), Row(re_table, Column(re_delete_button, re_edit_button)))
    u_lay = Row(reader, edit_lay)
    lay = Column(menu, u_lay)
    curdoc().add_root(lay)


####登場人物の自動追加のための関数、widgetたち####    

auto_ch = Button(label='登場人物の候補を抽出', button_type='success', width=200)
LABELS = ["Option 1", "Option 2", "Option 3"]

checkbox_group = CheckboxGroup(labels=[], active=[0, 1], width = 200)
add_ch = Button(label='追加', button_type='success', width = 70)

#表示しているページからまだ追加されていない関係を抽出する関数
def auto_character():
    peoples = [i['people'] for i in important.people_list]
    use_text = novel_dict[important.title].row_text[important.pageNumber]
    ginza_set = set()
    """
    m = MeCab.Tagger("-Ochasen")
    mecab_text = m.parse(use_text)
    #print(mecab_text)
    mecab_line = mecab_text.split('\n')[:-1]
    mecab_set = set()
    for i in mecab_line:
        i_me = i.split('\t')
        if not (i_me[0]=='EOS'):
            hinsi=i_me[3]
            hinsi_list = hinsi.split('-')
            if hinsi_list[0]=='名詞':
                mecab_set.add(i_me[0])

    #print(len(mecab_set))
    people_ca = mecab_set & set(people_candidate)
    print(people_ca)
    ginza_set = set()
    for i in people_ca:
        if not(i in peoples):ginza_set.add(i)

    
    
    
    print('固有表現')
    """
    doc = nlp(use_text)
    ginza_only_set=set()
    for ent in doc.ents:
        #print(ent.text, ent.label_)
        if (ent.label_ in ['Person', 'Position_Vocation']) and (not('\u3000' in ent.text)) and (not(ent.text in peoples)):
            ginza_set.add(ent.text)
            ginza_only_set.add(ent.text)

    print('ginzaの結果:', ginza_only_set)
    
    checkbox_group.labels = list(ginza_set)
    curdoc().clear()
    lay2 = Column(Row(forward_button, backward_button), auto_ch,checkbox_group)
    checkbox_group.active = list(range(len(list(ginza_set))))
    book_lay = Column(bookmark, add_ch)
    menu = Row(lay1,lay2, book_lay, jump_mark, input_info, import_down)
    lay = Column(menu, reader)
    curdoc().add_root(lay)
    novel_coloring(list(ginza_set), 'palegreen')

#wordsに含まれた単語をcolorで色をつける
def novel_coloring(words, color):
    text = important.textline[page_slider.value]
    for people in words:
        to = str('<span style="background-color:'+color+'">'+people+'</span>')
        #text = re.findall(people, to, text)
        text=text.replace(people, to)

    p.text = text
        
#登場人物の候補のなかで選択されたものだけ本文で色づけする関数
def checkbox_group_renderer(attr, new, old):
    active = checkbox_group.active
    new_ch = checkbox_group.labels
    active_person = [new_ch[i] for i in active]
    novel_coloring(active_person, 'palegreen')

checkbox_group.on_change('active',checkbox_group_renderer)

#選択された登場人物候補を登場人物として追加
def add_ch_renderer():
    new_ch = checkbox_group.labels
    active = checkbox_group.active
    for i in range(len(new_ch)):
        if i in active:
            novel_dict[important.title].people_list.append({'people':new_ch[i], 'line':page_slider.value})
            important.people_list=novel_dict[important.title].people_list 
    save()
    curdoc().clear()
    lay2 = Column(Row(forward_button, backward_button), auto_ch)
    menu = Row(lay1,lay2, bookmark, jump_mark, input_info, import_down)
    lay = Column(menu, reader)
    curdoc().add_root(lay)

    p.text = important.textline[page_slider.value]

add_ch.on_click(add_ch_renderer)
        
auto_ch.on_click(auto_character)


####システムを動かす上で格納したい情報を取得する####
if os.path.exists('dokusyo-aozora/data/novel_dict.binaryfile'):
    print('既にデータがあるのでロードします')
    with open('dokusyo-aozora/data/novel_dict.binaryfile', 'rb') as sp:
        novel = pickle.load(sp)
    novel_dict = novel[0]
    novel_list = novel[1]
    already_novels = novel[2]
    already_import.options = novel_list
else:    
    print('新たにデータを生成します')
    novel_list = ['none'] #ダウンロード済みのタイトルのリスト
    novel_dict = {} #本のタイトルと
    already_novels = []

with open('dokusyo-aozora/data/people_candidate.txt') as f:
    people_candidate_txt = f.read()

people_candidate = people_candidate_txt.split('\n')
people_candidate = people_candidate[:-2]

####システムのレイアウトを作る関数たち####
lay1 = Column(page_slider, select_vis)
lay2 = Column(Row(forward_button, backward_button), auto_ch)
menu = Row(lay1,lay2, bookmark, jump_mark, input_info, import_down)
reader = Column(title, author, p)

lay = Column(menu, reader)


curdoc().add_root(lay)
print('レイアウト生成完了')


for i in novel_dict:
    path = novel_dict[i].graph_path
    path = path.replace('readerapp/', '')
    novel_dict[i].graph_path = 'dokusyo-aozora/'+path
    save()

"""
for i,j in zip(['銀河鉄道の夜','レ・ミゼラブル','はつ恋','こころ','そして誰もいなくなった','注文の多い料理店'],['readerapp/data/graph_data/銀河鉄道の夜','readerapp/data/graph_data/レ・ミゼラブル','readerapp/data/graph_data/はつ恋','readerapp/data/graph_data/こころ','readerapp/data/graph_data/そして誰もいなくなった']):
    novel_dict[i].graph_path = j
save()
"""