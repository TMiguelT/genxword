from abc import ABC, abstractmethod
from gi.repository import Pango, PangoCairo
import cairo

class Exporter(ABC):
    @abstractmethod
    @property
    def code(self):
        """
        Return a one-letter code that is used to activate this exporter
        """

    @abstractmethod
    def export(self, name, puzzle, filename, headings, rtl, key):
        """
        Export a puzzle in this class's format
        :param name: Crossword name
        :param puzzle: The ExportFile instance to export
        :param filename: The name of the file to output
        :param headings: Array with 2 elements containing the localised names for "Across" and "Down"
        :param rtl: If true, produce a crossword for a right-to-left language
        :param key: If true, produce the crossword key, otherwise produce the puzzle
        """

    @staticmethod
    def wrap(text, width=80):
        """
        Returns `text`, but wrapped to `width` characters
        """
        lines = []
        for paragraph in text.split('\n'):
            line = []
            len_line = 0
            for word in paragraph.split():
                len_word = len(word)
                if len_line + len_word <= width:
                    line.append(word)
                    len_line += len_word + 1
                else:
                    lines.append(' '.join(line))
                    line = [word]
                    len_line = len_word + 1
            lines.append(' '.join(line))
        return '\n'.join(lines)

    def draw_img(self, name, context, px, xoffset, yoffset, rtl):
        for r in range(self.rows):
            for i, c in enumerate(self.grid[r]):
                if c != self.empty:
                    context.set_line_width(1.0)
                    context.set_source_rgb(0.5, 0.5, 0.5)
                    context.rectangle(xoffset+(i*px), yoffset+(r*px), px, px)
                    context.stroke()
                    context.set_line_width(1.0)
                    context.set_source_rgb(0, 0, 0)
                    context.rectangle(xoffset+1+(i*px), yoffset+1+(r*px), px-2, px-2)
                    context.stroke()
                    if '_key.' in name:
                        self.draw_letters(c, context, xoffset+(i*px)+10, yoffset+(r*px)+8, 'monospace 11')

        self.order_number_words()
        for word in self.wordlist:
            if rtl:
                x, y = ((self.cols-1)*px)+xoffset-(word[3]*px), yoffset+(word[2]*px)
            else:
                x, y = xoffset+(word[3]*px), yoffset+(word[2]*px)
            self.draw_letters(str(word[5]), context, x+3, y+2, 'monospace 6')


    def export_pdf(self, xwname, filetype, lang, rtl, width=595, height=842):

