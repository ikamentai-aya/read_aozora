from bokeh.plotting import figure
from bokeh.models import *
from graphviz import Digraph #有向グラフ
from xml.dom import minidom

#情報をgraphvisに入れてグラフを作成する
def make_graphvis(line_number, ch_list, re_list, graph_path):

    graph = Digraph(format='svg',
                    graph_attr={'size':"600,600"})

    graph.engine= 'sfdp'

    new_ch_list = [] #現在までに出てきている人のリスト
    for i in ch_list:
        if i['line'] <= line_number:
            new_ch_list.append(i['people'])
            #graph.node(i['people'])

    new_ch_size = dict()
    for i in new_ch_list:new_ch_size[i] = 100

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
        graph.edge(j_list[0],j_list[1],'')

    print(graph)

    save_path = graph_path +'/'+ str(line_number)

    graph.render(save_path)
    return save_path


#ノードリンク図の定義
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



# linkの方向を示す△の実装
head_source = ColumnDataSource(data=dict(xs=[], ys=[], color=[], line_color=[]))
head_glyph = Patches(xs="xs", ys="ys", fill_color='color', line_color='line_color', fill_alpha=0.7)
node_link.add_glyph(head_source, head_glyph)






