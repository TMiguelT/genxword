from . import Exporter
from abc import ABC, abstractmethod
from gi.repository import Pango, PangoCairo
import cairo


class ImageExporter(Exporter):
    @abstractmethod
    def get_surface(self, name, puzzle):
        pass

    def get_px(self):
        return 28

    def draw(self, name, puzzle, context, surface, rtl):
        px = self.get_px()
        context.set_source_rgb(1, 1, 1)
        context.rectangle(0, 0, 10+(puzzle.cols*px), 10+(puzzle.rows*px))
        context.fill()
        self.draw_img(name, context, 28, 5, 5, rtl)

    def export(self, name, puzzle, filename, headings, rtl, key):
        surface = self.get_surface(name, puzzle)
        context = cairo.Context(surface)
        self.draw(name, puzzle, context, surface, rtl)

    def draw_letters(self, text, context, xval, yval, fontdesc):
        context.move_to(xval, yval)
        layout = PangoCairo.create_layout(context)
        font = Pango.FontDescription(fontdesc)
        layout.set_font_description(font)
        layout.set_text(text, -1)
        PangoCairo.update_layout(context, layout)
        PangoCairo.show_layout(context, layout)

class SvgExporter(ImageExporter):
    @property
    def code(self):
        return 's'

    def draw(self, *args, surface, context, **kwargs):
        super().draw(*args, surface=surface, context=context, **kwargs)
        context.show_page()
        surface.finish()

    def get_surface(self, name, puzzle):
        px = self.get_px()
        return cairo.SVGSurface(name, 10 + (puzzle.cols * px), 10 + (puzzle.rows * px))

class PngExporter(ImageExporter):
    def draw(self, *args, surface, name, **kwargs):
        super().draw(*args, surface=surface, name=name, **kwargs)
        surface.write_to_png(name)

    def get_surface(self, name, puzzle):
        px = self.get_px()
        return cairo.ImageSurface(cairo.FORMAT_RGB24, 10 + (puzzle.cols * px), 10 + (puzzle.rows * px))

    @property
    def code(self):
        return 'n'

class PdfExporter(ImageExporter):
    def export(self, name, puzzle, filename, headings, rtl, key):
        px, xoffset, yoffset = 28, 36, 72
        surface = cairo.PDFSurface(name, width, height)
        context = cairo.Context(surface)
        context.set_source_rgb(1, 1, 1)
        context.rectangle(0, 0, width, height)
        context.fill()
        context.save()
        sc_ratio = float(width-(xoffset*2))/(px*self.cols)
        if self.cols <= 21:
            sc_ratio, xoffset = 0.8, float(1.25*width-(px*self.cols))/2
        context.scale(sc_ratio, sc_ratio)
        self.draw_img(name, context, 28, xoffset, 80, rtl)
        context.restore()
        context.set_source_rgb(0, 0, 0)
        self.draw_letters(xwname, context, round((width-len(xwname)*10)/2), yoffset/2, 'Sans 14 bold')
        x, y = 36, yoffset+5+(self.rows*px*sc_ratio)
        clues = self.wrap(self.legend(lang))
        self.draw_letters(lang[0], context, x, y, 'Sans 12 bold')
        for line in clues.splitlines()[3:]:
            if y >= height-(yoffset/2)-15:
                context.show_page()
                y = yoffset/2
            if line.strip() == lang[1]:
                if self.cols > 17 and y > 700:
                    context.show_page()
                    y = yoffset/2
                y += 8
                self.draw_letters(lang[1], context, x, y+15, 'Sans 12 bold')
                y += 16
                continue
            self.draw_letters(line, context, x, y+18, 'Serif 9')
            y += 16
        context.show_page()
        surface.finish()

