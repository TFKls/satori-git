from satori.core.export._topsort import topsort

class RightsOptions(object):
    all_options = []

    def __init__(self, model, meta, bases):
        self.model = model
        self.meta = meta
        self.bases = bases
        self.child_models = {}

        self.all_options.append(self)
        
        self.id_column = 'id'
        for parent in model._meta.parents:
            self.id_column = model._meta.parents[parent].get_attname()[:-3]
            parent._rights_meta.child_models[model] = model._meta.parents[parent].related_query_name()

    def preprocess(self):
        meta = self.meta
        bases = self.bases
        self.rights = set(getattr(meta, 'rights', []))
        
        self.inherit = {}

        right_pairs = []

        for right in self.rights:
            self.inherit[right] = set([right] + getattr(meta, 'inherit_' + right, []))

            for second_right in self.inherit[right]:
                if second_right != right:
                    right_pairs.append((second_right, right))

        for right in topsort(right_pairs):
            for second_right in set(self.inherit[right]):
                self.inherit[right].update(self.inherit[second_right])

    def process(self):
        meta = {}
        
        for name in dir(self.meta):
            if not name.startswith('__'):
                meta[name] = getattr(self.meta, name)
        
        self.rights = set(meta.pop('rights', []))
            
        for base in self.bases:
            self.rights.update(base.rights)

        self.inherit_field = meta.pop('inherit_parent', None)
        for base in self.bases:
            if base.inherit_field and self.inherit_field:
                raise RuntimeError("Cannot inherit rights from two parents")
            if base.inherit_field:
                self.inherit_field = base.inherit_field

        self.inherit_model = None
        self.inhetit_field_nullable = False
        if self.inherit_field:
            for field in self.model._meta.fields:
                if field.name == self.inherit_field:
                    self.inherit_model = field.related.parent_model
                    self.inherit_field_nullable = field.null

            if not self.inherit_model:
                raise RuntimeError("Cannot find field to parent")

        self.inherit_parent_require = meta.pop('inherit_parent_require', None)
        for base in self.bases:
            if base.inherit_parent_require and self.inherit_parent_require:
                raise RuntimeError("Cannot require several rights from parent")
            if base.inherit_parent_require:
                self.inherit_parent_require = base.inherit_parent_require

        if self.inherit_parent_require and not self.inherit_field:
            raise RuntimeError("Cannot require rights from parent without parent specified")    

        self.inherit = {}
        self.inherit_parent = {}
        self.inherit_global = {}

        right_pairs = []

        for right in self.rights:
            self.inherit[right] = set([right] + meta.pop('inherit_' + right, []))
            self.inherit_parent[right] = set(meta.pop('inherit_parent_' + right, []))
            self.inherit_global[right] = set(meta.pop('inherit_global_' + right, []))

            for second_right in set(self.inherit_global[right]):
                self.inherit_global[right].update(Global._rights_meta.inherit[second_right])

            for base in self.bases:
                self.inherit[right].update(base.inherit.get(right, {}))
                self.inherit_parent[right].update(base.inherit_parent.get(right, {}))
                self.inherit_global[right].update(base.inherit_global.get(right, {}))

            for second_right in self.inherit[right]:
                if second_right != right:
                    right_pairs.append((second_right, right))

        for right in topsort(right_pairs):
            for second_right in set(self.inherit[right]):
                self.inherit[right].update(self.inherit[second_right])
                self.inherit_parent[right].update(self.inherit_parent[second_right])
                self.inherit_global[right].update(self.inherit_global[second_right])

        self.local_inherit = {}
        self.local_inherit_parent = {}
        self.local_inherit_global = {}

        for right in self.rights:
            self.local_inherit[right] = set(self.inherit[right])
            self.local_inherit_parent[right] = set(self.inherit_parent[right])
            self.local_inherit_global[right] = set(self.inherit_global[right])

            for base in self.bases:
                self.local_inherit[right].difference_update(base.inherit.get(right, {}))
                self.local_inherit_parent[right].difference_update(base.inherit_parent.get(right, {}))
                self.local_inherit_global[right].difference_update(base.inherit_global.get(right, {}))

            if self.local_inherit_parent[right] and not self.inherit_field:
                raise RuntimeError("Cannot inherit rights from parent without parent specified")

        if meta:
            raise RuntimeError("Unknown parameters in RightsMeta: " + ",".join(meta.keys()))

    def add_local_rights_nodes(self, node, rights, path, used, used_parent, used_global):
        all_rights = set()
        all_parent_rights = set()
        all_global_rights = set()
        my_path = path or ['id']

        for right in rights:
            all_rights.update(self.inherit[right])
            all_parent_rights.update(self.inherit_parent[right])
            all_global_rights.update(self.inherit_global[right])

        all_rights.difference_update(used)
        all_parent_rights.difference_update(used_parent)
        all_global_rights.difference_update(used_global)

        if all_rights or all_parent_rights or all_global_rights:
            local_node = ConnectNode([RightNode(path, right, nullable=True, trim=False) for right in all_rights], 'OR')
            local_node = local_node | ConnectNode([GlobalRightNode(right) for right in all_global_rights], 'OR')
            
            if self.inherit_field and all_parent_rights:
                local_node = local_node | self.inherit_model._rights_meta.get_rights_node(
                        all_parent_rights, path + [self.inherit_field], True, used_parent, set(), used_global | all_global_rights)

            local_node = IsNullNode(path, False, trim=False) & local_node;

            node = node | local_node

        for child in self.child_models:
            child._rights_meta.add_local_rights_nodes(node, rights, path + [self.child_models[child]], used | all_rights, used_parent | all_parent_rights, used_global | all_global_rights)

        return node

    def add_local_require_nodes(self, node, path):
        if self.inherit_parent_require:
            local_node = IsNullNode(path, True, trim=False) | self.inherit_model._rights_meta.get_rights_node(
                    set([self.inherit_parent_require]), path + [self.inherit_field], True, set(), set(), set())
            if self.inherit_field_nullable:
                local_node = local_node | IsNullNode(path + [self.inherit_field], True, trim=True)
            node = node & local_node
        else:
            for child in self.child_models:
                node = child._rights_meta.add_local_require_nodes(node, path + [self.child_models[child]])

        return node

    def get_rights_node(self, rights, path, nullable, used, used_parent, used_global):
        all_rights = set()
        all_parent_rights = set()
        all_global_rights = set()

        for right in rights:
            all_rights.update(self.inherit[right])
            all_parent_rights.update(self.inherit_parent[right])
            all_global_rights.update(self.inherit_global[right])

        all_rights.difference_update(used)
        all_parent_rights.difference_update(used_parent)
        all_global_rights.difference_update(used_global)

        my_path = path or ['id']
        local_node = ConnectNode([RightNode(my_path, right, nullable=nullable, trim=True) for right in all_rights], 'OR')
        local_node = local_node | ConnectNode([GlobalRightNode(right) for right in all_global_rights], 'OR')
        
        if self.inherit_field and all_parent_rights:
            local_node = local_node | self.inherit_model._rights_meta.get_rights_node(
                    all_parent_rights, path + [self.inherit_field], nullable or self.inherit_field_nullable, set(), set(), used_global | all_global_rights)

        for child in self.child_models:
            local_node = child._rights_meta.add_local_rights_nodes(local_node, rights, path + [self.child_models[child]], used | all_rights, used_parent | all_parent_rights, used_global | all_global_rights)

        if self.inherit_parent_require:
            require_node = self.inherit_model._rights_meta.get_rights_node(
                    set([self.inherit_parent_require]), path + [self.inherit_field], nullable or self.inherit_field_nullable, set(), set(), set())
            if self.inherit_field_nullable:
                require_node = require_node | IsNullNode(path + [self.inherit_field], True, trim=True)

            local_node = local_node & require_node
        else:
            for child in self.child_models:
                local_node = child._rights_meta.add_local_require_nodes(local_node, path + [self.child_models[child]])

        return local_node

    def create_nodes(self):
        self.nodes = {}
        for right in self.rights:
            self.nodes[right] = self.get_rights_node([right], [], False, set(), set(), set())


class SatoriNode(object):
    def prepare_joins(self, query, field_list, nullable=False, trim=False):
        field, source, opts, join_list, last, _ = query.setup_joins(
            field_list, query.get_meta(), query.get_initial_alias(), False)
        query.promote_alias_chain(join_list, nullable)
        col, _, join_list = query.trim_joins(source, join_list, last, trim)
        return (join_list[-1], col)
    @staticmethod
    def connect(first, second, connector):
        if not (isinstance(first, SatoriNode) and isinstance(second, SatoriNode)):
            raise TypeError()
        if (isinstance(first, ConnectNode) and isinstance(second, ConnectNode)
                and (first.connector == connector) and (second.connector == connector)):
            return ConnectNode(first.children + second.children, connector)
        if isinstance(first, ConnectNode) and (first.connector == connector):
             return ConnectNode(first.children + [second], connector)
        if isinstance(second, ConnectNode) and (second.connector == connector):
             return ConnectNode([first] + second.children, connector)
        return ConnectNode([first, second], connector)
    def __or__(self, other):
        return SatoriNode.connect(self, other, 'OR')
    def __ror__(self, other):
        return SatoriNode.connect(other, self, 'OR')
    def __and__(self, other):
        return SatoriNode.connect(self, other, 'AND')
    def __rand__(self, other):
        return SatoriNode.connect(other, self, 'AND')


class ConnectNode(SatoriNode):
    def __init__(self, children=None, connector=None):
        super(SatoriNode, self).__init__()
        self.children = children or []
        self.connector = connector
    def prepare(self, query):
        return ConnectNode([c.prepare(query) for c in self.children], self.connector)
    def as_sql(self):
        if self.children:
            return '(' + (' ' + self.connector + ' ').join(child.as_sql() for child in self.children) + ')'
        else:
            if self.connector == 'OR':
                return 'FALSE'
            elif self.connector == 'AND':
                return 'TRUE'
            else:
                return '()'


class PreparedRightNode(SatoriNode):
    def __init__(self, table, column, right):
        super(PreparedRightNode, self).__init__()
        self.table = table
        self.column = column
        self.right = right
    def as_sql(self):
        return 'EXISTS (SELECT * FROM user_privs WHERE user_privs.entity_id = {0}.{1} AND user_privs.right = \'{2}\')'.format(self.table, self.column, self.right)


class RightNode(SatoriNode):
    def __init__(self, field_list, right, nullable=False, trim=False):
        super(RightNode, self).__init__()
        self.field_list = field_list
        self.right = right
        self.nullable = nullable
        self.trim = trim
    def prepare(self, query):
        table, column = self.prepare_joins(query, self.field_list, self.nullable, self.trim)
        return PreparedRightNode(table, column, self.right)


class GlobalRightNode(SatoriNode):
    def __init__(self, right):
        super(GlobalRightNode, self).__init__()
        self.right = right
    def prepare(self, query):
        return self
    def as_sql(self):
        return 'EXISTS (SELECT * FROM user_privs WHERE user_privs.entity_id = {0} AND user_privs.right = \'{1}\')'.format(Global.get_instance().id, self.right)


class PreparedIsNullNode(SatoriNode):
    def __init__(self, table, column, value):
        super(PreparedIsNullNode, self).__init__()
        self.table = table
        self.column = column
        self.value = value
    def as_sql(self):
        return '{0}.{1} IS {2} NULL'.format(self.table, self.column, '' if self.value else 'NOT')


class IsNullNode(SatoriNode):
    def __init__(self, field_list, value, trim=False):
        super(IsNullNode, self).__init__()
        self.field_list = field_list
        self.value = value
        self.trim = trim
    def prepare(self, query):
        table, column = self.prepare_joins(query, self.field_list, True, self.trim)
        return PreparedIsNullNode(table, column, self.value)


def init():
    global Global

    from satori.core.models import Global

    Global._rights_meta.preprocess()

    pairs = []
        
    for options in RightsOptions.all_options:
        pairs.append((None, options))
        for parent in options.model._meta.parents:
            pairs.append((parent._rights_meta, options))

    for options in topsort(pairs)[1:]:
        options.process()
    for options in RightsOptions.all_options:
        options.create_nodes()
