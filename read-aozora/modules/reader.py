from bokeh.models import Paragraph,TextInput, PreText, Button, Slider, Dropdown, Select, Div, HoverTool, TapTool, BoxSelectTool, LinearColorMapper, BasicTicker, PrintfTickFormatter, ColorBar, CheckboxButtonGroup, Rect, CheckboxGroup, DataTable, TableColumn, GlyphRenderer, Spinner, GraphRenderer, Ellipse,MultiLine, NodesAndLinkedEdges, EdgesAndLinkedNodes,StaticLayoutProvider, Text
from bokeh.models import Range1d
from bokeh.plotting import figure, output_file, show, curdoc
from bokeh.models import ColumnDataSource
from bokeh.layouts import Column, Row
from bokeh import events

import re
import os.path,glob

reset_button = Button(label='', button_type='success', width=70)
def reset_renderer():
    print('Hello')

reset_button.on_click(reset_renderer)

p = Div(text='[タイトル]',width=600, height=900) #本文
title = Div(text='[著者]', width =600, height = 15) #本のタイトル表示
author = Div(text='[本文　小説を選択してください]', width =600, height = 50) #本の作者表示

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