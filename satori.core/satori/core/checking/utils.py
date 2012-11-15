# vim:ts=4:sts=4:sw=4:expandtab

class RestTable(object):
    def __init__(self, *cols):
        super(RestTable, self).__init__()
        self.col_width = [col[0] for col in cols]
        self.col_name = [col[1] for col in cols]
        self.row_separator = '+' + '+'.join(['-' * width for width in self.col_width]) + '+\n'
        self.header_separator = '+' + '+'.join(['=' * width for width in self.col_width]) + '+\n'
        self.header_row = self.generate_row(*self.col_name)

    def escape(self, item):
        ret = []
        for c in unicode(item):
            if c.isalnum() or c.isspace():
                ret.append(c)
            else:
                ret.append(u'\\')
                ret.append(c)
        return u''.join(ret)

    def unescape(self, item):
        ret = []
        esc = False
        for c in unicode(item):
            if esc:
                ret.append(c)
                esc = False;
            if c == u'\\':
                esc = True;
            else:
                ret.append(c)
        return u''.join(ret)

    def generate_row(self, *items):
        if len(items) != len(self.col_width):
            raise RuntimeError('Item count not equal to column count.')

        max_count = 0
        row_items = []

        for i in range(len(items)):
            item = unicode(items[i]).strip()

            width = self.col_width[i]
            row_item = []
            first = 0
            while first < len(item):
                pos = item.rfind(' ', first, first + width)
                if first + width >= len(item):
                    item_elem = item[first:]
                    first = len(item)
                elif pos == -1:
                    if item[first + width - 1] == u'\\':
                        item_elem = item[first : first+width-1]
                        first += width-1
                    else:
                        item_elem = item[first : first+width]
                        first += width
                else:
                    item_elem = item[first : pos]
                    first = pos + 1
                item_elem = '|' + item_elem + ' ' * (width - len(item_elem))
                row_item.append(item_elem)
            row_items.append(row_item)
            if max_count < len(row_item):
                max_count = len(row_item)

        for i in range(len(items)):
            if len(row_items[i]) < max_count:
                filling = '|' + ' ' * self.col_width[i]
                while len(row_items[i]) < max_count:
                    row_items[i].append(filling)

        return ''.join([''.join([row_items[j][i] for j in range(len(items))]) + '|\n' for i in range(max_count)])

    def parse_row(self, row):
        res = []
        start = []
        pos = 0
        for i in range(len(self.col_width)):
            start.append(1+pos)
            res.append([])
            pos = pos+1+self.col_width[i]
        for line in row.split('\n'):
            for i in range(len(res)):
                res[i].append(line[start[i]:start[i]+self.col_width[i]].strip())
        return [ ' '.join(r).strip() for r in res ]

class Transaction(object):
    @staticmethod
    def enter():
        transaction.enter_transaction_management(True)
        transaction.managed(True)

    @staticmethod
    def rollback():
        transaction.rollback()

    @staticmethod
    def commit_and_leave():
        transaction.commit()
        transaction.managed(False)
        transaction.leave_transaction_management()

