from bokeh.plotting import figure
from bokeh.models import (Ellipse, GraphRenderer, StaticLayoutProvider,MultiLine,EdgesAndLinkedNodes, Text,Arrow,Legend,LegendItem,
                          HoverTool,NodesAndLinkedEdges,BoxSelectTool,TapTool,ColumnDataSource, Range1d, NormalHead, Patches)


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






