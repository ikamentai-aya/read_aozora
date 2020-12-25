from bokeh.models import (Ellipse, GraphRenderer, StaticLayoutProvider,MultiLine,EdgesAndLinkedNodes, Text,
                          HoverTool,NodesAndLinkedEdges,BoxSelectTool,TapTool,ColumnDataSource, Range1d)
from bokeh.plotting import figure
import math

hm_source = ColumnDataSource(data = dict(x = [], y = [], colors = []))

hm_axis_source = ColumnDataSource(data = dict(xaxis = []))
#hm = figure(title="Categorical Heatmap", x_range = [], y_range = [])
#heat_axis = xlsxPerson['person']
hm = figure(title="Categorical Heatmap", x_range = [], y_range = [])
hm.rect('x', 'y', color='colors', width=1, height=1, source = hm_source)
hm.xaxis.major_label_orientation = math.pi/2
hm.xaxis.axis_label = 'target'
hm.yaxis.axis_label = 'source'
    
edge_hover_tool = HoverTool(tooltips=[("source","@y"),("target","@x")])
hm.add_tools(edge_hover_tool)
