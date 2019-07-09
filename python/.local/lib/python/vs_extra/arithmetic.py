import ast, vapoursynth as vs                                      # noqa: E401


class __nv(ast.NodeVisitor):
    """Simple expression parser."""

    def __init__(self):
        self.tokens = []

    def visit(self, expr):
        super(__nv, self).visit(expr)
        return self.tokens

    def visit_BoolOp(self, node):
        for val in node.values:
            self.visit(val)
        self.visit(node.op)

    def visit_IfExp(self, node):
        self.visit(node.test)
        self.visit(node.body)
        self.visit(node.orelse)
        self.tokens.append('?')

    def visit_Call(self, node):
        for arg in node.args:
            self.visit(arg)
        self.visit(node.func)

    def visit_UnaryOp(self, node):
        self.visit(node.operand)
        self.visit(node.op)

    def visit_BinOp(self, node):
        self.visit(node.left)
        self.visit(node.right)
        self.visit(node.op)

    def visit_Compare(self, node):
        self.visit(node.left)
        self.visit(node.comparators[0])
        self.visit(node.ops[0])

        args, ops =           \
            node.comparators, \
            node.ops[1:]

        args = zip(args[:-1], args[1:])

        for O, (A, B) in zip(ops, args):
            self.visit(A)
            self.visit(B)
            self.visit(O)
            self.tokens.append('and')

    def visit_Add(self, node):
        self.tokens.append('+')
        super(__nv, self).generic_visit(node)

    def visit_UAdd(self, node):
        self.tokens.append('+')
        super(__nv, self).generic_visit(node)

    def visit_Sub(self, node):
        self.tokens.append('-')
        super(__nv, self).generic_visit(node)

    def visit_USub(self, node):
        self.tokens.append('-')
        super(__nv, self).generic_visit(node)

    def visit_Div(self, node):
        self.tokens.append('/')
        super(__nv, self).generic_visit(node)

    def visit_Mult(self, node):
        self.tokens.append('*')
        super(__nv, self).generic_visit(node)

    def visit_Eq(self, node):
        self.tokens.append("=")
        super(__nv, self).generic_visit(node)

    def visit_Lt(self, node):
        self.tokens.append("<")
        super(__nv, self).generic_visit(node)

    def visit_Gt(self, node):
        self.tokens.append(">")
        super(__nv, self).generic_visit(node)

    def visit_LtE(self, node):
        self.tokens.append("<=")
        super(__nv, self).generic_visit(node)

    def visit_GtE(self, node):
        self.tokens.append(">=")
        super(__nv, self).generic_visit(node)

    def visit_Or(self, node):
        self.tokens.append('or')
        super(__nv, self).generic_visit(node)

    def visit_And(self, node):
        self.tokens.append('and')
        super(__nv, self).generic_visit(node)

    def visit_BitXor(self, node):
        self.tokens.append('xor')
        super(__nv, self).generic_visit(node)

    def visit_Not(self, node):
        self.tokens.append('not')
        super(__nv, self).generic_visit(node)

    def visit_Name(self, node):
        self.tokens.append(node.id)
        super(__nv, self).generic_visit(node)

    def visit_Num(self, node):
        self.tokens.append(str(node.n))
        super(__nv, self).generic_visit(node)

    def visit_Expr(self, node):
        super(__nv, self).generic_visit(node)


def Expr(expr: str, clips, **kwargs):
    """Wrapper for VapourSynth Expr function."""
    expr = ' '.join(__nv().visit(ast.parse(expr)))
    return vs.core.std.Expr(clips, expr, **kwargs)
