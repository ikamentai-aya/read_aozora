
import re
import zipfile
import urllib.request
import os.path,glob
import pickle
import shutil
import math

import numpy as np
from bokeh.models import *
from bokeh.plotting import figure, curdoc
from bokeh.layouts import Column, Row
from bokeh import events

####他のサブファイルで定義したものの読み込み#####
from class1 import Important, Group
from modules.auto import auto_all
from modules.reader import reset_button, p, title, author, convert
#from modules.node import node_link, node_source, edge_source, source, provider
from modules.node import make_graphvis
from modules.matrix import hm
from modules.arrange import ch_source, ch_columns, ch_table, re_source, re_columns, re_table
############################################

####グラフ描画に必要なライブラリ##########
from graphviz import Digraph #有向グラフ
from xml.dom import minidom
#####################################

####自然言語処理に必要なライブラリ#######
import sys
import spacy
from spacy import displacy
nlp = spacy.load('ja_ginza')
##############################


####システム内で使うデータ構造の定義#######
important = Important('','',[],[],800,0,[],[],[],[],'', dict())
gr_path = 'read-aozora/data/graph_data/'
ch_frequency_dict = dict() #登場人物の出現頻度の辞書
people_candidate = [] #自動抽出ででた登場人物のリスト
global initial_set
initial_set = False
global center_set
center_set = False
novel_dict = dict()
novel_list = []
already_novels = []
#####################################

####小説の本文####
novel = Column(title, author,p, name = 'novel')


####本を読むための機能#####   
forward = Button(label='▷', button_type='success', width=100, name='forward')
backward = Button(label='◁', button_type='success', width=100, name='backward')
page_slider = Slider(start=0, end=len(important.textline)+1, value=1, step=1, title="現在の段落", width=200, name = 'page_slider')
########################

####読む本を選ぶためのwidget#####
import_down = Dropdown(label="小説の選択", button_type="warning", menu=['none','ダウンロード済み', '新たにダウンロード'], width=200)
already_import = Select(title="小説", value="none", options=['none'], width=200)
text_input= TextInput(value="default",title="URLを入力してください:", width=200) #新たにダウンロードする本のURLを打ち込むTextInput
finish_text = PreText(text='', width=100, height=20)
novel_decide = Button(label='小説を追加', button_type='success', width=100)
select_book = Column(children = [import_down ], name = 'select_book')

#########

####しおりをつける機能####
bookmark = Button(label='しおり', button_type='success', width=100, name ='bookmark')
jump_mark = Dropdown(label="しおりに飛ぶ", button_type="warning", menu=[], width = 200, name = 'jump_mark')

####情報追加#####
input_select = Dropdown(label="情報追加", button_type="warning", menu=['none','登場人物追加', '関係性追加'], width=200)
info_input = Column(children = [input_select], name = 'info_input')

def input_select_renderer(event):
    global info_input
    
    if event.item == '登場人物追加':
        info_input.children = [input_select, chracter_input, decide_ch]

    elif event.item == '関係性追加':
        info_input.children = [input_select, source_input, target_input, relation_input, emotion_input, decide_re]
    else:
        info_input.children = [input_select]
    
####登場人物の追加####
chracter_input = TextInput(value="default",title="人物を入力してください", width = 200)
decide_ch = Button(label='以上の人物を追加', button_type='success', width = 200)


#####関係の追加#####
source_input = Select(title='誰から',value='none',options=['none'], width=200)
target_input = Select(title='誰への',value='none',options=['none'], width=200)
relation_input = TextInput(value='default',title='どんな関係', width=200)
emotion_input = Slider(start=1, end=5, value=1, step=1, title="好意的か（5:好意的、1:否定的）", width=200)
decide_re = Button(label='以上の関係を追加', button_type='success', width=200)

####可視化の選択####
select_vis = Select(title="可視化の選択", value="表示なし", options=['表示なし', '人物相関図', '人物相関表','編集画面'], width=200, name="select_vis")

####登場人物の自動抽出####
auto_ch_button = Button(label='登場人物の候補を抽出', button_type='success', width=200)
LABELS = ["Option 1", "Option 2", "Option 3"]
checkbox_group = CheckboxGroup(labels=[], active=[0, 1], width = 200)
add_ch = Button(label='追加', button_type='success', width = 70)
auto_ch = Column(auto_ch_button, name = 'auto_ch')

####可視化のタブ等####
vue = Column(children=[], name = 'vue')
colors = ['#76487A', '#9F86BC', '#F9BF33', '#F1B0B2', '#CB5266']
color_bar = figure(title = '', x_range = ['嫌い','好きじゃない','どっちでもない','好き','大好き'], y_range=['1'], width = 600, height = 70, tools = [])
color_bar.rect(x= ['嫌い','好きじゃない','どっちでもない','好き','大好き'], y=['1','1','1','1','1'], width=1, height=1,line_color=None, fill_color=colors)

####人物相関図のツール#####
show_range_spinner = Spinner(title="直近何ページの関係か", low=1, high=1, step=1, value=1, width=50)
show_main_people = Select(title="この人を中心とする", value="none", options=['none'], width=100)
show_people_check = CheckboxGroup(labels=[], active=[], width = 100)
first_choice = False
###############

####情報編集画面のツール####
frequency_color = ['white','#dcf8dc','#b8f1b8','#95ea95','#4edc4e','#23b123','#1d8d1d','#156a15']
frequency_count = [[0],[1,2],[3,4],[5,6],[7,8],[9,10],[11,12]]
ch_delete_button = Button(label='消去', button_type='success', width =100)
ch_edit_button = Button(label='変更を保存', button_type='success', width=100)
ch_plus_button = Button(label='+', button_type='success', width=50, background='white')
ch_minus_button = Button(label='-', button_type='success', width=50, background='white')
re_delete_button = Button(label='消去', button_type='success', width =100)
re_edit_button = Button(label='変更を保存', button_type='success', width=100)
re_plus_button = Button(label='+', button_type='success', width=50, background='white')
re_minus_button = Button(label='-', button_type='success', width=50, background='white')

####登場人物の自動抽出に関連するツール####
auto_ch_button = Button(label='登場人物の候補を抽出', button_type='success', width=200)
LABELS = ["Option 1", "Option 2", "Option 3"]
checkbox_group = CheckboxGroup(labels=[], active=[0, 1], width = 200)
add_ch = Button(label='追加', button_type='success', width = 70)
auto_ch = Row(children = [auto_ch_button], name = 'auto_ch')
cancel_button = Button(label='キャンセル', button_type='success', width = 70)

####自動情報抽出####
auto_button = Button(label='自動情報抽出', button_type='success', width=200)
auto_text = PreText(text='', width=100, height=20)
all_auto = Column(auto_button, auto_text, name='all_auto')


####システムの初期動作関数#####
def start():

    global novel_dict, novel_list, people_candidate, already_import, already_novels

    ####システムを動かす上で格納したい情報を取得する####
    if os.path.exists('read-aozora/data/novel_dict.binaryfile'):
        print('既にデータがあるのでロードします')
        with open('read-aozora/data/novel_dict.binaryfile', 'rb') as sp:
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

    with open('read-aozora/data/people_candidate.txt') as f:
        people_candidate_txt = f.read()

    people_candidate = people_candidate_txt.split('\n')
    people_candidate = people_candidate[:-2]

#小説の選択画面
def import_renderer(event):
    global select_book
    
    if event.item == 'ダウンロード済み':
        #select_book = Column(import_down, already_import, name='select_book')
        select_book.children = [import_down, already_import]

    elif event.item == '新たにダウンロード':
        select_book.children = [import_down, text_input, novel_decide, finish_text]

    else:
        select_book.children = [import_down]


####小説の読み込み関数####
def already_import_renderer(attr, old, new):
    if not (already_import.value == 'none'):
        
        global novel_dict, important, new_title, auto_text
        #global initial_set
        #initial_set=True
        #importantの書き換え
        new_title = already_import.value
        important = novel_dict[new_title]
        ch_frequency_dict = novel_dict[new_title].ch_freq
        ch_source.selected.indices = []

        auto_text.text = ""
        
        title.text = "<style> .info{font-size:15px;} </style>"+'<p class = "info">'+important.title+"<p/>"
        author.text = '<p class = "info">'+important.author+"<p/>"
        
        page_slider.end = len(important.textline)
        page_slider.value = important.pageNumber
        
        
        #matrixの調整
        global first_choice
        first_choice = True
        show_range_spinner.high = len(important.textline)
        show_range_spinner.value = len(important.textline)
        ch_now_list = []
        for i in important.people_list:
            if i['line'] <= page_slider.value:ch_now_list.append(i['people'])
        show_people_check.labels = ch_now_list
        show_people_check.active = list(range(len(ch_now_list)))
        first_choice= False
        
        #ブックマークの更新
        menu = []
        for i in novel_dict[important.title].bookMark:
            text = str(i)+' '
            for j in range(min([len(important.textline[i]), 30])):text += important.textline[i][j]
            text += '...'
            menu.append(text)
        
        jump_mark.menu = menu
        p.text = important.textline[important.pageNumber]

        #save()
        show_vis()
        
#url_getのsub　routin
def download(url):
    # データファイルをダウンロードする
    zip_file = 'read-aozora/data/aozora/' + re.split(r'/', url)[-1]

    urllib.request.urlretrieve(url, zip_file)

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
    check_path = 'read-aozora/data/aozora/' + paths
    
    #if not os.path.exists(check_path):
    if not (check_path in already_novels):
        print('Download URL')
        print('URL:',url)
        shutil.move(new_path, 'read-aozora/data/aozora')
        shutil.rmtree(dir)
        return check_path
        
    else:
        print('Download File exists')
        shutil.rmtree(dir)
        return 0

#小説のURLを入力されたら、小説をダウンロードして、読めるように整形する関数
def url_get(event):
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
        novel_dict[title] = Important(title, author, lines, row_lines,800, 0, [], [], [], [], g_path, dict())
        novel_list.append(title)
        already_import.options = novel_list
        save()
        finish_text.text = 'ダウンロードが完了しました'

####ページの移動関数####
def forward_renderer():
    head = important.pageNumber + 1
    if head <= page_slider.end:
        page_slider.value = head

def backward_renderer():
    head = important.pageNumber -1
    if head >= 0:
        page_slider.value = head

def page_slider_renderer(attr, new, old):

    head = page_slider.value
    important.pageNumber = head
    novel_dict[important.title].pageNumber = head
    p.text = important.textline[head]

    show_vis()
    save()

#########

####情報の追加####

#新しく登場人物としてデータに保存
def chracter_renderer():
    
    ch_list = []
    for i in novel_dict[important.title].people_list:
        ch_list.append(i['people'])
    if not (chracter_input.value in ch_list):
        novel_dict[important.title].people_list.append({'people':chracter_input.value, 'line':page_slider.value})
        important.people_list=novel_dict[important.title].people_list 
        save()
        show_vis()

#関係性としてデータに保存
def relation_renderer():
    
    new_dict = {'source':source_input.value, 'target':target_input.value, 'line':page_slider.value, 'emotion':emotion_input.value, 'relation':relation_input.value}
    novel_dict[important.title].relation_list.append(new_dict)

    #novel_dict[important.title].relation_list.append({'source':source_input.value, 'target':target_input.value, 'line':important['headNumber'], 'emotion':emotion_input.value, 'relation':relation_input.value})
    important.relation_list = novel_dict[important.title].relation_list
    save()
    show_vis()

##################3

####可視化の定義#####
def select_vis_renderer(attr, old, new):
    show_vis()
    
def show_vis():

    if select_vis.value == '表示なし':
        vue.children = []

    elif select_vis.value =='人物相関図':
        make_node_link()

    elif select_vis.value == '人物相関表':
        make_matrix()

    else:
        make_arrange()

####人物相関表図の作成####
#ノードリンク図を作成する関数
def make_node_link():
    p.text = important.textline[page_slider.value]
    save_path = make_graphvis(page_slider.value, important.people_list, important.relation_list, novel_dict[important.title].graph_path)
    import_graph_info(save_path)
    
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

    
    colors = ['#76487A', '#9F86BC', '#F9BF33', '#F1B0B2', '#CB5266']

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
    
    ###

    node_link = figure(title= '人物相関図', plot_height = 600, plot_width = 600)
    node_link.add_tools(HoverTool(tooltips=None), TapTool(), BoxSelectTool())
    node_link.xaxis.visible=False
    node_link.yaxis.visible=False


    graph = GraphRenderer()
        
    #graphのnode_rendererにデータ追加(Ellipse:楕円)
    node_source = graph.node_renderer.data_source
    node_source.data = dict(index = [], color = [], rx = [], ry = [])
    graph.node_renderer.glyph = Ellipse(height='ry', width='rx', fill_color='color')
        
    #エッジの追加（startの列、endの列）
    edge_source= graph.edge_renderer.data_source
    edge_source.data = dict(start=[],end=[], index = [], color = [], emotion = [], xs = [], ys=[])

    graph.edge_renderer.glyph = MultiLine(line_color='color', line_alpha=0.5, line_width=5)

    #interactionの追加

    graph.node_renderer.selection_glyph = Ellipse(height=10, width=15, fill_color='#F9BF33', fill_alpha=1.0)
    graph.node_renderer.nonselection_glyph = Ellipse(fill_color='white', fill_alpha=1.0)
    graph.node_renderer.hover_glyph = Ellipse(height=10, width=15, fill_color='#F9BF33',fill_alpha=1.0)
    graph.edge_renderer.selection_glyph = MultiLine(line_alpha=1.0, line_width=8, line_color='color')
    graph.edge_renderer.nonselection_glyph = MultiLine(line_alpha=0.7, line_width=5, line_color='gray')
    graph.edge_renderer.hover_glyph = MultiLine(line_alpha=1.0, line_width=8, line_color='color')
    graph.selection_policy = NodesAndLinkedEdges()
    graph.inspection_policy = EdgesAndLinkedNodes()

    #HoverToolの追加
    node_hover_tool = HoverTool(tooltips=[("person","@index")],renderers=[graph.node_renderer])
    edge_hover_tool = HoverTool(tooltips=[("start","@start"),("end","@end"),("index", "@index"), ('emotion', '@emotion')],renderers=[graph.edge_renderer])
    node_link.add_tools(node_hover_tool)
    node_link.add_tools(edge_hover_tool)

    #graph_layout = dict(zip(node_source.data['index'], zip(node_source.data['x'], node_source.data['y'])))
    graph.layout_provider = StaticLayoutProvider(graph_layout=dict())
    provider = graph.layout_provider

    node_link.renderers.append(graph)
        
    source = ColumnDataSource(data = dict(x=[], y=[], text=[]))
    glyph = Text(x="x", y="y", text="text", text_color="black",text_font_size = "9px", text_align="center")
    node_link.add_glyph(source, glyph)
    ###

    if not (x_list == []):
        print('レイアウト範囲変更')
        max_x = max(x_list)+1000; min_x = min(x_list)-1000
        max_y = max(y_list)+1000; min_y = min(y_list)-1000
        #global range_list
        #range_list = [min_x, max_x, min_y, max_y]

        node_link.x_range = Range1d(min_x, max_x)
        node_link.y_range = Range1d(min_y, max_y)
        #range_rool.x_range = Range1d(min_x, max_x)
        #range_rool.y_range = Range1d(min_y, max_y)
        print(node_link.x_range)
        



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
    vue.children = [color_bar, node_link]
    
####人物相関表を作るための補助関数####
def make_matrix_sub(center, check):
    line_number = page_slider.value 

    ch_now_list = show_people_check.labels
    relation_list = important.relation_list
    
    global initial_set
    global center_set


    if initial_set == True: 
        show_people_check.active = list(range(len(ch_now_list))) 

    re_now_list = []
    re_emotion_list = []
    start_line = max(page_slider.value - show_range_spinner.value, 0)#ここからの関係を写す

    main_people = show_main_people.value
    if check == False and main_people == 'none':
        show_people_check.active = list(range(len(ch_now_list)))


    if center == True:#中心人物が選択されている時
        center_set = True
        if main_people == 'none':
            print('noneが選ばれました')
            ch_show_list =set()
            for i in important.people_list:
                if (i['line'] >= start_line) and (i['line'] <= page_slider.value):ch_show_list.add(i['people'])
            for j in relation_list:
                if j['line'] >= start_line: 
                    ch_show_list.add(j['source'])
                    ch_show_list.add(j['target'])
                    re_now_list.append([j['source'], j['target']])
                    re_emotion_list.append([j['emotion'],j['relation'],j['line']])
            print('ここまでOK')
            ch_show_list = list(ch_show_list)
            print(ch_show_list)
            show_people_check.active = list(range(len(ch_now_list)))
            print(len(show_people_check.labels))
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
        center_set = False
    else:
        ch_show_list=[]

        for i in show_people_check.active:
            if i < len(ch_now_list):
                ch_show_list.append(ch_now_list[i])
        for j in relation_list:
            if (j['line'] <= page_slider.value) and (j['line'] >= start_line) and ((j['source'] in ch_show_list)and(j['target'] in ch_now_list)): 
                re_now_list.append([j['source'], j['target']])
                re_emotion_list.append([j['emotion'],j['relation'],j['line']])
        

    colors = ['#76487A', '#9F86BC', '#F9BF33', '#F1B0B2', '#CB5266'] 

    ch_show2 = ch_show_list
    ch_show_list = []
    for i in ch_now_list:
        if i in ch_show2:ch_show_list.append(i)
    
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
    toolList = ['tap', 'save']
    hm = figure( x_range = ch_show_list, y_range=ch_show_list[::-1], width = 600, height = 600, tools = toolList, x_axis_location="above")

    hm.xaxis.axis_label = '誰への'
    hm.yaxis.axis_label = '誰から'
    
    
    hm.xaxis.major_label_orientation = -math.pi/2
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

                vue.children = [Row(Column(hm, color_bar, st_text,st_table),Column(show_range_spinner, show_main_people, show_people_check))]

            else:
                vue.children = [Row(Column(hm, color_bar), Column(show_range_spinner, show_main_people, show_people_check))]
                
        else:
            vue.children = [Row(Column(hm,color_bar), Column(show_range_spinner, show_main_people, show_people_check))]
            

    hm.on_event(events.Tap, hmTap_callback)
    vue.children = [Row(Column(hm,color_bar), Column(show_range_spinner, show_main_people, show_people_check))]

def show_main_renderer(attr, old, new):
    global first_choice
    if first_choice == False:
        make_matrix_sub(True, False)

def show_people_renderer(attr, old, new):
    global first_choice
    if first_choice == False and center_set == False:
        print('show_people_renderer')
        make_matrix_sub(False, True)

def show_range_renderer(attr, old, new):
    global first_choice
    if first_choice == False:
        print('show_range_renderer')
        make_matrix_sub(False, False)

#人物相関表を選択されたときに表示する関数
def make_matrix():

    show_range_spinner.high = len(important.textline)
    
    ch_list = important.people_list
    ch_now_list = []
    
    for i in ch_list:
        if i['line'] <= page_slider.value: ch_now_list.append(i['people'])
    
    
    show_main_people.options = ['none']+ ch_now_list
    show_people_check.labels = ch_now_list 

    make_matrix_sub(False, False)


####人物相関表に関する関数####
#キャラクターを削除する関数
def ch_remove_renderer():
    selectionRow=ch_source.selected.indices
    for i in selectionRow:
        rm_people=ch_source.data['people'][i]
        rm_line=ch_source.data['line'][i]

        important.people_list.remove({'people':rm_people, 'line':rm_line})
        novel_dict[important.title].people_list=important.people_list
    make_person_fre()
    save()

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

    make_person_fre()
    save()

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

    make_person_fre()
    save()

#関係の編集の保存
def re_edit_renderer():
    new_relation = []
    for source, target, relation, emotion, line in zip(re_source.data['source'], re_source.data['target'], re_source.data['relation'], re_source.data['emotion'], re_source.data['line']):
        emotion = int(emotion)
        line = int(line)
        new_relation.append({'source':source, 'target':target, 'relation':relation, 'emotion':emotion, 'line':line})

    novel_dict[important.title].relation_list = new_relation
    important.relation_list = new_relation
    make_person_fre()
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

#登場人物編集表で選択された人物が変化した時
def ch_select_renderer(attr, old, new):
    make_person_fre()

#情報編集画面のレイアウトを作る関数
def make_person_fre():    
    person = [ch_source.data['people'][i] for i in ch_source.selected.indices]
    novel_coloring(person, 'yellow')
    for i in person:
        if not (i in ch_frequency_dict):
            frequency = []
            for page in important.textline:
                frequency.append(page.count(i))
            ch_frequency_dict[i] = frequency
        
    x_range=[str(i) for i in range(len(important.textline))]
    height = len(person)*10
    toolList = ['pan', 'box_zoom', 'lasso_select', 'poly_select', 'tap', 'reset', 'save']
    frequency_heat = figure(plot_width=700, plot_height=150, x_range=x_range, y_range=person, tools=toolList)
    
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

    if ch_source.selected.indices == []:
        vue.children = [Row(ch_plus_button, ch_minus_button), Row(ch_table, Column(ch_delete_button, ch_edit_button)),Row(re_plus_button, re_minus_button), Row(re_table, Column(re_delete_button, re_edit_button))]
    else:
        vue.children = [Row(ch_plus_button, ch_minus_button), Row(ch_table, Column(ch_delete_button, ch_edit_button)),frequency_heat,Row(re_plus_button, re_minus_button), Row(re_table, Column(re_delete_button, re_edit_button))]
    #save()

#編集のための表を作る関数
def make_arrange():
    
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

    print(ch_source.selected.indices)
    person = [ch_source.data['people'][i] for i in ch_source.selected.indices]
    novel_coloring(person, 'yellow')
    make_person_fre()
    
####情報の自動抽出に関する関数####
#表示しているページからまだ追加されていない関係を抽出する関数
def auto_character():
    peoples = [i['people'] for i in important.people_list]
    use_text = novel_dict[important.title].row_text[important.pageNumber]

    ginza_set = set()
    doc = nlp(use_text)
    ginza_only_set=set()
    for ent in doc.ents:
        if (ent.label_ in ['Person', 'Position_Vocation']) and (not('\u3000' in ent.text)) and (not(ent.text in peoples)):
            ginza_set.add(ent.text)
            ginza_only_set.add(ent.text)
    
    checkbox_group.labels = list(ginza_set)

    #レイアウトの変更
    auto_ch.children = [Column(auto_ch_button, Row(add_ch, cancel_button)), checkbox_group]
    checkbox_group.active = list(range(len(list(ginza_set))))
    
    novel_coloring(list(ginza_set), 'palegreen')

def all_auto_ch_renderer():
    auto_text.text = '情報抽出を開始しました'
    character_list, relation_list = auto_all(important.textline, important.people_list, important.relation_list)
    novel_dict[important.title].people_list = character_list
    important.people_list=character_list
    novel_dict[important.title].relation_list = relation_list
    important.relation_list=relation_list
    save()
    auto_text.text = '情報抽出を開始しました'

auto_button.on_click(all_auto_ch_renderer)

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


#選択された登場人物候補を登場人物として追加
def add_ch_renderer():
    new_ch = checkbox_group.labels
    active = checkbox_group.active
    for i in range(len(new_ch)):
        if i in active:
            novel_dict[important.title].people_list.append({'people':new_ch[i], 'line':page_slider.value})
            important.people_list=novel_dict[important.title].people_list 
    save()

    p.text = important.textline[page_slider.value]
    auto_ch.children = [auto_ch_button]
    show_vis()

#色付けを直す関数
def cancel_renderer():
    auto_ch.children = [auto_ch_button]
    novel_coloring([], 'white')

#現状の変化を保存する
def save():
    with open('read-aozora/data/novel_dict.binaryfile', 'wb') as sp:
        pickle.dump([novel_dict,novel_list, already_novels] , sp)


####関数の紐付け#####
import_down.on_click(import_renderer)
already_import.on_change('value', already_import_renderer)
novel_decide.on_click(url_get)
forward.on_click(forward_renderer)
backward.on_click(backward_renderer)
page_slider.on_change('value', page_slider_renderer)

input_select.on_click(input_select_renderer)
decide_ch.on_click(chracter_renderer)
decide_re.on_click(relation_renderer)
select_vis.on_change('value',select_vis_renderer)


####人物相関表に関するツール####
show_main_people.on_change('value', show_main_renderer)
show_people_check.on_change('active', show_people_renderer)
show_range_spinner.on_change('value', show_range_renderer)

####情報編集画面に関するツール####
ch_delete_button.on_click(ch_remove_renderer)
ch_edit_button.on_click(ch_edit_renderer)
ch_plus_button.on_click(ch_plus_renderer)
ch_minus_button.on_click(ch_minus_renderer)
ch_source.selected.on_change('indices', ch_select_renderer)
re_delete_button.on_click(re_remove_renderer)
re_edit_button.on_click(re_edit_renderer)
re_plus_button.on_click(re_plus_renderer)
re_minus_button.on_click(re_minus_renderer)

####情報抽出のに関する関数####
add_ch.on_click(add_ch_renderer) 
cancel_button.on_click(cancel_renderer)       
auto_ch_button.on_click(auto_character)
checkbox_group.on_change('active',checkbox_group_renderer)

start()

####HTMLへの受け渡し#####
doc = curdoc()

doc.add_root(forward)
doc.add_root(backward)
doc.add_root(page_slider)
doc.add_root(bookmark)
doc.add_root(jump_mark)
doc.add_root(select_book)

doc.add_root(select_vis)
doc.add_root(info_input)
doc.add_root(auto_ch)
doc.add_root(all_auto)

doc.add_root(novel)
doc.add_root(vue)



