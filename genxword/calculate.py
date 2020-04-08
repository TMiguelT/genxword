"""Calculate the crossword and export image and text files."""

# Authors: David Whitlock <alovedalongthe@gmail.com>, Bryan Helmig
# Crossword generator that outputs the grid and clues as a pdf file and/or
# the grid in png/svg format with a text file containing the words and clues.
# Copyright (C) 2010-2011 Bryan Helmig
# Copyright (C) 2011-2020 David Whitlock
#
# Genxword is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Genxword is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with genxword.  If not, see <http://www.gnu.org/licenses/gpl.html>.

import gi
gi.require_version('PangoCairo', '1.0')
gi.require_version('Pango', '1.0')

from gi.repository import Pango, PangoCairo
import random, time, cairo
from operator import itemgetter
from collections import defaultdict

class Crossword:
    def __init__(self, rows, cols, empty=' ', available_words=[]):
        self.rows = rows
        self.cols = cols
        self.empty = empty
        self.available_words = available_words
        self.let_coords = defaultdict(list)

    def prep_grid_words(self):
        self.current_wordlist = []
        self.let_coords.clear()
        self.grid = [[self.empty]*self.cols for i in range(self.rows)]
        self.available_words = [word[:2] for word in self.available_words]
        self.first_word(self.available_words[0])

    def compute_crossword(self, time_permitted=1.00):
        self.best_wordlist = []
        wordlist_length = len(self.available_words)
        time_permitted = float(time_permitted)
        start_full = float(time.time())
        while (float(time.time()) - start_full) < time_permitted:
            self.prep_grid_words()
            [self.add_words(word) for i in range(2) for word in self.available_words
             if word not in self.current_wordlist]
            if len(self.current_wordlist) > len(self.best_wordlist):
                self.best_wordlist = list(self.current_wordlist)
                self.best_grid = list(self.grid)
            if len(self.best_wordlist) == wordlist_length:
                break
        #answer = '\n'.join([''.join(['{} '.format(c) for c in self.best_grid[r]]) for r in range(self.rows)])
        answer = '\n'.join([''.join([u'{} '.format(c) for c in self.best_grid[r]])
                            for r in range(self.rows)])
        return answer + '\n\n' + str(len(self.best_wordlist)) + ' out of ' + str(wordlist_length)

    def get_coords(self, word):
        """Return possible coordinates for each letter."""
        word_length = len(word[0])
        coordlist = []
        temp_list =  [(l, v) for l, letter in enumerate(word[0])
                      for k, v in self.let_coords.items() if k == letter]
        for coord in temp_list:
            letc = coord[0]
            for item in coord[1]:
                (rowc, colc, vertc) = item
                if vertc:
                    if colc - letc >= 0 and (colc - letc) + word_length <= self.cols:
                        row, col = (rowc, colc - letc)
                        score = self.check_score_horiz(word, row, col, word_length)
                        if score:
                            coordlist.append([rowc, colc - letc, 0, score])
                else:
                    if rowc - letc >= 0 and (rowc - letc) + word_length <= self.rows:
                        row, col = (rowc - letc, colc)
                        score = self.check_score_vert(word, row, col, word_length)
                        if score:
                            coordlist.append([rowc - letc, colc, 1, score])
        if coordlist:
            return max(coordlist, key=itemgetter(3))
        else:
            return

    def first_word(self, word):
        """Place the first word at a random position in the grid."""
        vertical = random.randrange(0, 2)
        if vertical:
            row = random.randrange(0, self.rows - len(word[0]))
            col = random.randrange(0, self.cols)
        else:
            row = random.randrange(0, self.rows)
            col = random.randrange(0, self.cols - len(word[0]))
        self.set_word(word, row, col, vertical)

    def add_words(self, word):
        """Add the rest of the words to the grid."""
        coordlist = self.get_coords(word)
        if not coordlist:
            return
        row, col, vertical = coordlist[0], coordlist[1], coordlist[2]
        self.set_word(word, row, col, vertical)

    def check_score_horiz(self, word, row, col, word_length, score=1):
        cell_occupied = self.cell_occupied
        if col and cell_occupied(row, col-1) or col + word_length != self.cols and cell_occupied(row, col + word_length):
            return 0
        for letter in word[0]:
            active_cell = self.grid[row][col]
            if active_cell == self.empty:
                if row + 1 != self.rows and cell_occupied(row+1, col) or row and cell_occupied(row-1, col):
                    return 0
            elif active_cell == letter:
                score += 1
            else:
                return 0
            col += 1
        return score

    def check_score_vert(self, word, row, col, word_length, score=1):
        cell_occupied = self.cell_occupied
        if row and cell_occupied(row-1, col) or row + word_length != self.rows and cell_occupied(row + word_length, col):
            return 0
        for letter in word[0]:
            active_cell = self.grid[row][col]
            if active_cell == self.empty:
                if col + 1 != self.cols and cell_occupied(row, col+1) or col and cell_occupied(row, col-1):
                    return 0
            elif active_cell == letter:
                score += 1
            else:
                return 0
            row += 1
        return score

    def set_word(self, word, row, col, vertical):
        """Put words on the grid and add them to the word list."""
        word.extend([row, col, vertical])
        self.current_wordlist.append(word)

        horizontal = not vertical
        for letter in word[0]:
            self.grid[row][col] = letter
            if (row, col, horizontal) not in self.let_coords[letter]:
                self.let_coords[letter].append((row, col, vertical))
            else:
                self.let_coords[letter].remove((row, col, horizontal))
            if vertical:
                row += 1
            else:
                col += 1

    def cell_occupied(self, row, col):
        cell = self.grid[row][col]
        if cell == self.empty:
            return False
        else:
            return True

class ExportFile:
    """
    Represents a complete crossword, ready to export
    """
    def __init__(self, rows, cols, grid, wordlist, empty=' '):
        self.rows = rows
        self.cols = cols
        self.grid = grid
        self.wordlist = wordlist
        self.empty = empty

    def order_number_words(self):
        self.wordlist.sort(key=itemgetter(2, 3))
        count, icount = 1, 1
        for word in self.wordlist:
            word.append(count)
            if icount < len(self.wordlist):
                if word[2] == self.wordlist[icount][2] and word[3] == self.wordlist[icount][3]:
                    pass
                else:
                    count += 1
            icount += 1

    def create_files(self, name, save_format, lang, message):
        if Pango.find_base_dir(self.wordlist[0][0], -1) == Pango.Direction.RTL:
            [i.reverse() for i in self.grid]
            RTL = True
        else:
            RTL = False
        img_files = ''
        if 'p' in save_format:
            self.export_pdf(name, '_grid.pdf', lang, RTL)
            self.export_pdf(name, '_key.pdf', lang, RTL)
            img_files += name + '_grid.pdf ' + name + '_key.pdf '
        if 'l' in save_format:
            self.export_pdf(name, 'l_grid.pdf', lang, RTL, 612, 792)
            self.export_pdf(name, 'l_key.pdf', lang, RTL, 612, 792)
            img_files += name + 'l_grid.pdf ' + name + 'l_key.pdf '
        if 'n' in save_format:
            self.create_img(name + '_grid.png', RTL)
            self.create_img(name + '_key.png', RTL)
            img_files += name + '_grid.png ' + name + '_key.png '
        if 's' in save_format:
            self.create_img(name + '_grid.svg', RTL)
            self.create_img(name + '_key.svg', RTL)
            img_files += name + '_grid.svg ' + name + '_key.svg '
        if 'n' in save_format or 's' in save_format:
            self.clues_txt(name + '_clues.txt', lang)
            img_files += name + '_clues.txt'
        if message:
            print(message + img_files)

    def word_bank(self):
        temp_list = list(self.wordlist)
        random.shuffle(temp_list)
        return 'Word bank\n' + ''.join([u'{}\n'.format(word[0]) for word in temp_list])

    def legend(self, lang):
        outStrA, outStrD = u'\nClues\n{}\n'.format(lang[0]), u'{}\n'.format(lang[1])
        for word in self.wordlist:
            if word[4]:
                outStrD += u'{:d}. {}\n'.format(word[5], word[1])
            else:
                outStrA += u'{:d}. {}\n'.format(word[5], word[1])
        return outStrA + outStrD

    def clues_txt(self, name, lang):
        with open(name, 'w') as clues_file:
            clues_file.write(self.word_bank())
            clues_file.write(self.legend(lang))
