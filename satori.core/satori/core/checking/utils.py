# vim:ts=4:sts=4:sw=4:expandtab

class RestTable(object):
    def __init__(self, *cols):
        super(RestTable, self).__init__()
        self.col_width = [col[0] for col in cols]
        self.col_name = [col[1] for col in cols]
        self.row_separator = '+' + '+'.join(['-' * width for width in self.col_width]) + '+\n'
        self.header_separator = '+' + '+'.join(['=' * width for width in self.col_width]) + '+\n'
        self.header_row = self.generate_row(*self.col_name)

    def generate_row(self, *items):
        if len(items) != len(self.col_width):
            raise RuntimeError('Item count not equal to column count.')

        max_count = 0
        row_items = []

        for i in range(len(items)):
            item = unicode(items[i])
            width = self.col_width[i]
            row_item = []
            first = 0
            while first < len(item):
                pos = item.rfind(' ', first, first + width)
                if first + width >= len(item):
                    item_elem = item[first:]
                    first = len(item)
                elif pos == -1:
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

