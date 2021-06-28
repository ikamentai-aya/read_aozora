from bokeh.models import Paragraph,TextInput, PreText, Button, Slider, Dropdown, Select, Div, HoverTool, TapTool, BoxSelectTool, LinearColorMapper, BasicTicker, PrintfTickFormatter, ColorBar, CheckboxButtonGroup, Rect, CheckboxGroup, DataTable, TableColumn, GlyphRenderer, Spinner, GraphRenderer, Ellipse,MultiLine, NodesAndLinkedEdges, EdgesAndLinkedNodes,StaticLayoutProvider, Text
from bokeh.models import Range1d
from bokeh.plotting import figure, output_file, show, curdoc
from bokeh.models import ColumnDataSource
from bokeh.layouts import Column, Row
from bokeh import events

reset_button = Button(label='', button_type='success', width=70)
def reset_renderer():
    print('Hello')

reset_button.on_click(reset_renderer)

p = Div(text='',width=600, height=900) #本文
title = Div(text='', width =600, height = 15) #本のタイトル表示
author = Div(text='', width =600, height = 50) #本の作者表示

