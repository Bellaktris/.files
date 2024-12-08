class Expressionsv2(Dashboard.Module):
    """Watch user expressions."""

    def __init__(self):
        self.number = 1
        self.table = {}
        self.xdict = {}

        self.xdict_fn = (lambda x:
            self.xdict[x] if x in self.xdict else int(x))

    def label(self):
        return 'Expressions'

    def lines(self, term_width, style_changed):
        out = []
        remap, t = {}, 1
        titems = sorted(self.table.items())

        for number, expression in titems:
            try:
                value = to_string(gdb.parse_and_eval(expression))
            except gdb.error as e:
                value = ansi(e, R.style_error)

            remap[number], t = t, t + 1
            number = ansi(t - 1, R.style_selected_2)

            expression = ansi(expression, R.style_low)
            out.append('[{}] {} = {}'.format(number, expression, value))

        del self.table, self.xdict
        self.table, self.xdict = {}, {}

        for k, (_, v) in enumerate(titems):
            self.table[k] = v
            self.xdict[v] = k

        return out

    def watch(self, arg):
        try:
            int(arg)
        except:
            if arg:
                if arg in self.xdict:
                    return

                self.table[self.number] = arg
                self.xdict[arg] = self.number
                self.number += 1
            else:
                raise Exception('Specify an expression')

    def unwatch(self, arg):
        if arg:
            try:
                del self.table[self.xdict_fn(arg)]

                if arg in self.xdict:
                    del self.xdict[arg]
                else:
                    for key, value in self.xdict.items():
                        if value == int(arg):
                            del self.xdict[key]; return
            except:
                raise Exception('Expression not watched')
        else:
            raise Exception('Specify an identifier')

    def clear(self, arg):
        self.table.clear()

    def commands(self):
        return {
            'watch': {
                'action': self.watch,
                'doc': 'Watch an expression.',
                'complete': gdb.COMPLETE_EXPRESSION
            },
            'unwatch': {
                'action': self.unwatch,
                'doc': 'Stop watching an expression by id.',
                'complete': gdb.COMPLETE_EXPRESSION
            },
            'clear': {
                'action': self.clear,
                'doc': 'Clear all the watched expressions.'
            }
        }
