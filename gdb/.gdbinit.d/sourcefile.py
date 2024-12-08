class Sourcefile(Dashboard.Module):
    """Show the program source code, if available."""

    def __init__(self):
        self.file_name = None

    def label(self):
        return 'Sourcefile'

    def lines(self, term_width, style_changed):
        if self.output_path is None:
            return []

        # skip if the current thread is not stopped
        if not gdb.selected_thread().is_stopped():
            return []

        # try to fetch the current line (skip if no line information)
        frame = gdb.selected_frame()

        if not frame.is_valid():
            return []

        sal = frame.find_sal()
        current_line = sal.line

        if current_line == 0:
            if os.path.islink(self.output_path):
                os.unlink(self.output_path)

            if os.path.exists(self.output_path):
                os.remove(self.output_path)

            os.symlink(self.output_path + '.none', self.output_path)

            with open(self.output_path + '.data', 'w') as file:
                file.write("1\n")

            return []

        # reload the source file if changed
        file_name = sal.symtab.fullname()

        bps = filter(lambda x: x.is_valid(), gdb.breakpoints())
        bps = map(lambda x: gdb.decode_line(x.location)[1], list(bps)[1:])

        bps = [x for y in bps for x in y if x.is_valid()]
        bps = ["%d" % x.line for x in bps if x.symtab.fullname() == file_name]

        if not os.path.exists(self.output_path + '.none'):
            with open(self.output_path + '.none', 'w') as file:
                file.write("/* Source file unavailable... */")

        with open(self.output_path + '.data', 'w') as file:
            if len(bps) > 0:
                file.write("%d\n" % current_line + '\n'.join(bps))
            else:
                file.write("%d\n" % current_line)

        if (file_name != self.file_name):
            self.file_name = file_name

            if os.path.islink(self.output_path):
                os.unlink(self.output_path)

            if os.path.exists(self.output_path):
                os.remove(self.output_path)

            if os.path.exists(file_name):
                os.symlink(self.file_name, self.output_path)
            else:
                os.symlink(self.output_path + '.none', self.output_path)

        return []

    def attributes(self):
        return {
            'output_path': {
                'doc': 'Path for setting source file link.',
                'default': None,
                'type': str,
            },
        }
