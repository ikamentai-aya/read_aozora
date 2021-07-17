from bokeh.models import *

ch_source=ColumnDataSource(data=dict(people=[], line=[]))

ch_columns = [
        TableColumn(field="people", title="人物名"),
        TableColumn(field="line", title="初登場ページ"),
    ]
ch_table = DataTable(source=ch_source, columns=ch_columns, width=600, height=200, editable = True, scroll_to_selection = True, selectable = 'checkbox')

re_source=ColumnDataSource(data=dict(source=[], target=[], relation=[], emotion = [], line=[]))
re_columns = [
    TableColumn(field="source", title="誰から"),
    TableColumn(field="target", title="誰への"),
    TableColumn(field="relation", title="関係"),
    TableColumn(field="emotion", title="好感度"),
    TableColumn(field="line", title="ページ")
]
re_table = DataTable(source=re_source, columns=re_columns, width=600, height=200, editable = True, scroll_to_selection = True, selectable =True)


