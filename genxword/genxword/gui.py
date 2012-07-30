# -*- coding: utf-8 -*-

# Authors: David Whitlock <alovedalongthe@gmail.com>, Bryan Helmig
# Crossword generator that outputs the grid and clues as a pdf file and/or
# the grid in png/svg format with a text file containing the words and clues.
# Copyright (C) 2010-2011 Bryan Helmig
# Copyright (C) 2011-2012 David Whitlock
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/gpl.html>.

import os
from gi.repository import Gtk, Pango
from .control import Genxword
from . import calculate

ui_info = """
<ui>
  <menubar name='MenuBar'>
    <menu action='FileMenu'>
      <menuitem action='New'/>
      <menuitem action='Open'/>
      <separator/>
      <menuitem action='Quit'/>
    </menu>
    <menu action='CrosswordMenu'>
      <menuitem action='Create'/>
      <menuitem action='Incgsize'/>
      <menuitem action='Save'/>
      <separator/>
      <menuitem action='EditGsize'/>
    </menu>
    <menu action='SaveOptsMenu'>
      <menuitem action='SaveA4'/>
      <menuitem action='Saveletter'/>
      <menuitem action='Savepng'/>
      <menuitem action='Savesvg'/>
    </menu>
    <menu action='HelpMenu'>
      <menuitem action='Help'/>
      <menuitem action='About'/>
    </menu>
  </menubar>
  <toolbar name='ToolBar'>
    <toolitem action='New'/>
    <toolitem action='Open'/>
    <separator action='Sep1'/>
    <toolitem action='Create'/>
    <toolitem action='Incgsize'/>
    <separator action='Sep2'/>
    <toolitem action='Save'/>
    <separator action='Sep3'/>
    <toolitem action='Help'/>
  </toolbar>
</ui>
"""

class Genxinterface(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title='genxword-gtk')

        self.set_default_size(650, 550)
        self.set_default_icon_name('genxword-gtk')
        self.calc_first_time = True
        self.saveformat = ''
        self.words = ''
        self.gsize = False

        self.grid = Gtk.Grid()
        self.add(self.grid)
        self.grid.set_border_width(6)
        self.grid.set_row_spacing(6)
        self.grid.set_column_spacing(6)

        action_group = Gtk.ActionGroup('gui_actions')
        self.add_main_actions(action_group)
        self.add_opts_actions(action_group)
        uimanager = self.create_ui_manager()
        uimanager.insert_action_group(action_group)
        menubar = uimanager.get_widget('/MenuBar')
        self.grid.attach(menubar, 0, 0, 6, 1)
        toolbar = uimanager.get_widget('/ToolBar')
        self.grid.attach(toolbar, 0, 1, 6, 1)

        self.textview_win()
        self.bottom_row()

    def add_main_actions(self, action_group):
        action_filemenu = Gtk.Action('FileMenu', '_Word list', None, None)
        action_group.add_action(action_filemenu)

        action_xwordmenu = Gtk.Action('CrosswordMenu', '_Crossword', None, None)
        action_group.add_action(action_xwordmenu)

        action_helpmenu = Gtk.Action('HelpMenu', '_Help', None, None)
        action_group.add_action(action_helpmenu)

        action_new = Gtk.Action('New', 'New word list', 'Create a new word list', Gtk.STOCK_NEW)
        action_new.connect('activate', self.new_wlist)
        action_group.add_action_with_accel(action_new, None)

        action_open = Gtk.Action('Open', 'Open word list', 'Open an existing word list', Gtk.STOCK_OPEN)
        action_open.connect('activate', self.open_wlist)
        action_group.add_action_with_accel(action_open, None)

        action_create = Gtk.Action('Create', 'Create crossword', 'Calculate the crossword', Gtk.STOCK_EXECUTE)
        action_create.connect('activate', self.create_xword)
        action_group.add_action_with_accel(action_create, '<control>G')

        action_incgsize = Gtk.Action('Incgsize', 'Recalculate',
            'Increase the grid size and recalculate the crossword', Gtk.STOCK_REDO)
        action_incgsize.connect('activate', self.incgsize)
        action_group.add_action_with_accel(action_incgsize, '<control>R')

        action_save = Gtk.Action('Save', 'Save', 'Save crossword', Gtk.STOCK_SAVE)
        action_save.connect('activate', self.save_xword)
        action_group.add_action_with_accel(action_save, None)

        action_help = Gtk.ToggleAction('Help', 'Help', 'Switch between the help page and the main view', Gtk.STOCK_HELP)
        action_help.connect('toggled', self.help_page)
        action_group.add_action_with_accel(action_help, 'F1')

        action_about = Gtk.Action('About', 'About', None, Gtk.STOCK_ABOUT)
        action_about.connect('activate', self.about_dialog)
        action_group.add_action(action_about)

        action_quit = Gtk.Action('Quit', 'Quit', None, Gtk.STOCK_QUIT)
        action_quit.connect('activate', self.quit_app)
        action_group.add_action_with_accel(action_quit, None)

    def add_opts_actions(self, action_group):
        action_optsmenu = Gtk.Action('SaveOptsMenu', '_Save options', None, None)
        action_group.add_action(action_optsmenu)

        save_A4 = Gtk.ToggleAction('SaveA4', 'Save as A4 pdf', None, None)
        save_A4.connect('toggled', self.save_options, 'p')
        action_group.add_action(save_A4)

        save_letter = Gtk.ToggleAction('Saveletter', 'Save as letter pdf', None, None)
        save_letter.connect('toggled', self.save_options, 'l')
        action_group.add_action(save_letter)

        save_png = Gtk.ToggleAction('Savepng', 'Save as png', None, None)
        save_png.connect('toggled', self.save_options, 'n')
        action_group.add_action(save_png)

        save_svg = Gtk.ToggleAction('Savesvg', 'Save as svg', None, None)
        save_svg.connect('toggled', self.save_options, 's')
        action_group.add_action(save_svg)

        edit_gsize = Gtk.ToggleAction('EditGsize', 'Choose the grid size', None, None)
        edit_gsize.connect('toggled', self.set_gsize)
        action_group.add_action(edit_gsize)

    def create_ui_manager(self):
        uimanager = Gtk.UIManager()
        uimanager.add_ui_from_string(ui_info)
        accelgroup = uimanager.get_accel_group()
        self.add_accel_group(accelgroup)
        return uimanager

    def textview_win(self):
        scrolledwindow = Gtk.ScrolledWindow()
        scrolledwindow.set_hexpand(True)
        scrolledwindow.set_vexpand(True)
        self.grid.attach(scrolledwindow, 0, 2, 6, 1)

        self.textview = Gtk.TextView()
        self.textview.set_border_width(6)
        fontdesc = Pango.FontDescription('serif')
        self.textview.modify_font(fontdesc)
        self.textbuffer = self.textview.get_buffer()
        self.tag_mono = self.textbuffer.create_tag('mono', font='monospace')
        scrolledwindow.add(self.textview)

    def text_edit_wrap(self, edit, wrap=Gtk.WrapMode.NONE):
        self.textview.set_editable(edit)
        self.textview.set_cursor_visible(edit)
        self.textview.set_wrap_mode(wrap)

    def bottom_row(self):
        self.enter_name = Gtk.Entry()
        self.enter_name.set_text('Name of crossword')
        self.enter_name.set_tooltip_text('Choose the name of your crossword')
        self.enter_name.set_icon_from_stock(Gtk.EntryIconPosition.SECONDARY, Gtk.STOCK_CLEAR)
        self.enter_name.connect('icon-press', self.entry_cleared)
        self.grid.attach(self.enter_name, 0, 3, 2, 1)

        nwords_label = Gtk.Label('Number of words')
        self.grid.attach(nwords_label, 2, 3, 1, 1)

        adjustment = Gtk.Adjustment(50, 10, 500, 5, 10, 0)
        self.choose_nwords = Gtk.SpinButton()
        self.choose_nwords.set_adjustment(adjustment)
        self.choose_nwords.set_update_policy(Gtk.SpinButtonUpdatePolicy.IF_VALID)
        self.choose_nwords.set_tooltip_text('Choose the number of words you want to use')
        self.grid.attach(self.choose_nwords, 3, 3, 1, 1)

        gsize_label = Gtk.Label('Grid size')
        self.grid.attach(gsize_label, 4, 3, 1, 1)

        self.choose_gsize = Gtk.Entry()
        self.choose_gsize.set_text('17,17')
        self.choose_gsize.set_width_chars(8)
        gsize_tip = 'Choose the crossword grid size\nGo to the Crossword menu to enable this option'
        self.choose_gsize.set_tooltip_text(gsize_tip)
        self.choose_gsize.set_sensitive(False)
        self.grid.attach(self.choose_gsize, 5, 3, 1, 1)

    def entry_cleared(self, entry, position, event):
        self.enter_name.set_text('')
        self.enter_name.grab_focus()

    def save_options(self, button, name):
        if button.get_active():
            self.saveformat += name
        else:
            self.saveformat = self.saveformat.replace(name, '')

    def new_wlist(self, button):
        self.text_edit_wrap(True)
        self.textbuffer.set_text(self.words)
        self.calc_first_time = True

    def open_wlist(self, button):
        dialog = Gtk.FileChooserDialog('Please choose a file', self,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        self.add_filters(dialog)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            with open(dialog.get_filename()) as infile:
                data = infile.read()
            self.text_edit_wrap(True)
            self.textbuffer.set_text(data)
        dialog.destroy()
        self.calc_first_time = True

    def add_filters(self, dialog):
        filter_text = Gtk.FileFilter()
        filter_text.set_name('Text files')
        filter_text.add_mime_type('text/plain')
        dialog.add_filter(filter_text)

    def calc_xword(self):
        save_recalc = ('\nIf you want to save this crossword, press the Save button.\n'
        'If you want to recalculate the crossword, press the Calculate button.\n'
        'To increase the grid size and then recalculate the crossword,\n'
        'press the Increase grid size button.')
        calc = calculate.Crossword(self.nrow, self.ncol, '-', self.wlist)
        self.textbuffer.set_text(calc.compute_crossword())
        self.add_tag(self.textbuffer, self.tag_mono, 0, -1)
        self.textbuffer.insert_at_cursor(save_recalc)
        self.choose_gsize.set_text(str(self.nrow) + ',' + str(self.ncol))
        self.best_word_list = calc.best_word_list
        self.best_grid = calc.best_grid

    def create_xword(self, button):
        self.text_edit_wrap(False)
        if self.calc_first_time:
            buff = self.textview.get_buffer()
            self.words = buff.get_text(buff.get_start_iter(), buff.get_end_iter(), False)
            nwords = self.choose_nwords.get_value_as_int()
            gen = Genxword()
            gen.wlist(self.words.splitlines(), nwords)
            self.wlist = gen.word_list
            gen.grid_size(True)
            if self.gsize:
                gen.check_grid_size(self.choose_gsize.get_text())
            self.nrow, self.ncol = gen.nrow, gen.ncol
            self.calc_xword()
            self.calc_first_time = False
        else:
            self.calc_xword()

    def incgsize(self, button):
        self.nrow += 2;self.ncol += 2
        self.calc_xword()

    def set_gsize(self, button):
        self.gsize = button.get_active()
        self.choose_gsize.set_sensitive(button.get_active())

    def save_xword(self, button):
        self.xwordname = self.enter_name.get_text()
        if self.xwordname != 'Name of crossword' and self.saveformat:
            dialog = Gtk.FileChooserDialog('Please choose a folder', self,
                Gtk.FileChooserAction.SELECT_FOLDER,
                (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                 'Select', Gtk.ResponseType.OK))
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                os.chdir(dialog.get_filename())
            else:
                return 0
            dialog.destroy()
            exp = calculate.Exportfiles(self.nrow, self.ncol, self.best_grid, self.best_word_list)
            exp.create_files(self.xwordname, self.saveformat, True)
            with open(self.xwordname + '_wlist.txt', 'w') as wlist_file:
                wlist_file.write(self.words)
            self.textbuffer.set_text('Your crossword files have been saved in\n' + os.getcwd())
            self.enter_name.set_text('Name of crossword')
            self.words = ''
        else:
            text = ('Please fill in the name of the crossword and the format you want it saved in.\n'
                    'Go to the Save options menu to choose the format.\nThen click on the Save button again.')
            self.textbuffer.set_text(text)

    def help_page(self, button):
        if button.get_active():
            self.text_editable = self.textview.get_editable()
            self.text_edit_wrap(False, Gtk.WrapMode.WORD)
            helpbuffer = self.textbuffer.new(None)
            self.textview.set_buffer(helpbuffer)
            helpbuffer.set_text(self.help_text())
            tag_title = helpbuffer.create_tag('title', font='sans bold 12')
            tag_subtitle = helpbuffer.create_tag('subtitle', font='sans bold')
            self.add_tag(helpbuffer, tag_title, 0, 1)
            for startline in (6, 22, 25, 28, 31, 34):
                self.add_tag(helpbuffer, tag_subtitle, startline, startline+1)
        else:
            self.textview.set_buffer(self.textbuffer)
            self.text_edit_wrap(self.text_editable)

    def help_text(self):
        try:
            with open('/usr/local/share/genxword/help_page') as help_file:
                return help_file.read()
        except:
            return 'Sorry, we cannot find what you asked for.'

    def add_tag(self, buffer_name, tag_name, startline, endline):
        start = buffer_name.get_iter_at_line(startline)
        end = buffer_name.get_iter_at_line(endline)
        buffer_name.apply_tag(tag_name, start, end)

    def about_dialog(self, button):
        license = ('This program is free software: you can redistribute it and/or modify'
        'it under the terms of the GNU General Public License as published by'
        'the Free Software Foundation, either version 3 of the License, or'
        '(at your option) any later version.\n\n'
        'This program is distributed in the hope that it will be useful,'
        'but WITHOUT ANY WARRANTY; without even the implied warranty of'
        'MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the'
        'GNU General Public License for more details.\n\n'
        'You should have received a copy of the GNU General Public License'
        'along with this program.  If not, see http://www.gnu.org/licenses/gpl.html')
        about = Gtk.AboutDialog()
        about.set_program_name('genxword-gtk')
        about.set_version('0.4.6')
        about.set_license(license)
        about.set_wrap_license(True)
        about.set_comments('A crossword generator')
        about.set_authors(['David Whitlock <alovedalongthe@gmail.com>', 'Bryan Helmig'])
        about.set_website('https://github.com/riverrun/genxword/wiki/genxword-gtk')
        about.set_website_label('genxword-gtk wiki')
        about.set_logo_icon_name('genxword-gtk')
        about.run()
        about.destroy()

    def quit_app(self, widget):
        Gtk.main_quit()

def main():
    win = Genxinterface()
    win.connect('delete-event', Gtk.main_quit)
    win.show_all()
    Gtk.main()
