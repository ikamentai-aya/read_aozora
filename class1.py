class Important:
    def __init__(self, title, author, textline, row_text, max_length, pageNumber, bookMark, people_list, relation_list, graph_path, ch_freq):
        self.title = title #小説のタイトル
        self.author = author #小説の作者
        self.textline = textline #小説の文の集合
        self.row_text = row_text
        self.max_length = max_length #最大で何文字まで表示するか
        self.pageNumber = pageNumber
        self.bookMark = bookMark #しおりの集合
        self.people_list = people_list #登場人物の集合
        self.relation_list = relation_list #関係性のリスト
        self.graph_path = graph_path
        self.ch_freq = ch_freq

