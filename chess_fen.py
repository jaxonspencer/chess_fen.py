import os, sys
import hashlib
import PyQt4.QtCore
import PyQt4.QtGui

# To execute a command-line test:
# export TEST_ANKI_FEN='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
# python chess_fen.py

# In anki mode, this enables a few verbose messages
# export TEST_ANKI_FEN_VERBOSE=1

# Some settings
px_cell_width = 45
white_cell_color = (0xc6, 0xc3, 0x63)
black_cell_color = (0x73, 0xa2, 0x6b)

# With fen-string as input, visit each cell of the chessboard and
# return the figure for each cell and its coordinates
class gen_next:
  def __init__(self, s_fen, px_step):
    self.s_fen   = s_fen
    self.px_step = px_step
    self.s_idx   = 0
    self.n_empty = 0
    self.x       = 0
    self.y       = 0

  def get_next(self):
    fig = '?'
    if not self.n_empty:
      if self.s_idx < len(self.s_fen):
        fig = self.s_fen[self.s_idx]
        if '/' != fig:
          self.s_idx   = self.s_idx + 1
          self.n_empty = '12345678'.find(fig) + 1
    if self.n_empty:
      self.n_empty = self.n_empty - 1
      fig = '?'
    cur_x = self.x
    self.x = cur_x + self.px_step
    return (fig, cur_x, self.y)

  def eol(self):
    self.s_idx = self.s_fen.find('/', self.s_idx) + 1
    self.x = 0
    self.y = self.y + self.px_step

#
# Images of figures. See chess_fen_media/README.
#
letter_to_picture = {}
def load_figures(media_dir):
  def load_figure(ch, path_part):
    png_file = os.path.join(media_dir, 'Chess_'+path_part+'45.png')
    letter_to_picture[ch] = PyQt4.QtGui.QPixmap(png_file)
  for ch in ('k', 'q', 'r', 'b', 'n', 'p'):
    load_figure(ch.upper(), ch+'lt')
    load_figure(ch, ch+'dt')

#
# From FEN to a picture
#
def generate_board(s_fen):
  px_width = px_cell_width * 8
  pixmap = PyQt4.QtGui.QPixmap(px_width, px_width)
  p = PyQt4.QtGui.QPainter()
  p.begin(pixmap)
  c = PyQt4.QtGui.QColor(*white_cell_color)
  p.fillRect(0, 0, px_width, px_width, c)
  pe = p.pen()
  pe.setColor(PyQt4.QtCore.Qt.black)
  pe.setWidth(2)
  p.setPen(pe)
  c = PyQt4.QtGui.QColor(*black_cell_color)
  g = gen_next(s_fen, px_cell_width)
  black_cell = 0
  for i in range(0,8):
    for j in range(0,8):
      (letter, x, y) = g.get_next()
      if black_cell:
        p.fillRect(x, y, px_cell_width, px_cell_width, c)
      black_cell = not black_cell
      pic = letter_to_picture.get(letter, None)
      if pic:
        p.drawPixmap(x, y, pic)
    g.eol()
    black_cell = not black_cell
  px_offset = 0
  for i in range(0,9):
    p.drawLine(px_offset, 0,         px_offset, px_width)
    p.drawLine(0,         px_offset, px_width,  px_offset)
    px_offset = px_offset + px_cell_width
  p.end()
  return pixmap

#
# FEN to file
#
def fen_to_file(s_fen, out_dir, stdout):
  s_file = hashlib.md5(s_fen).hexdigest()
  s_file = os.path.join(out_dir, s_file + '.png')
  if os.path.isfile(s_file):
    if stdout:
      print >>stdout, 'Already exists:', s_file
    return s_file                                          # return
  if not os.path.isdir(out_dir):
    os.mkdir(out_dir)
  pixmap = generate_board(s_fen)
  pixmap.save(s_file)
  if stdout:
    print >>stdout, 'Created:', s_file
  return s_file

#
# Command-line (test) mode
#
s_fen = os.environ.get('TEST_ANKI_FEN', '').strip()
if s_fen:
  print >>sys.stdout, 'fen:', s_fen
  app = PyQt4.QtGui.QApplication(sys.argv)
  load_figures('chess_fen_media')
  fen_to_file(s_fen, '.', sys.stdout)
  sys.exit(0)                                              # exit

stdout = None
if os.environ.get('TEST_ANKI_FEN_VERBOSE', 0):
  stdout = sys.stdout
  
#
# Anki mode
#
import re
from anki.hooks import addHook
from aqt import mw

load_figures(os.path.join(mw.pm.addonFolder(), 'chess_fen_media'))

regexps = {
    "fen": re.compile(r"\[fen\](?P<notation>(.+?))\[/fen\]", re.DOTALL | re.IGNORECASE),
    "side_to_move": re.compile(r"(?<= )[bw]", re.DOTALL | re.IGNORECASE),
    }

def fen_mungeQA(html, type, fields, model, data, col):
  for match in regexps['fen'].finditer(html):
    s_file = fen_to_file(match.group('notation'), col.media.dir(), stdout)
    px_width = 8 * px_cell_width
    s_img = '<img src="%s" width="%d" height="%d" border="1" />' % (s_file, px_width, px_width)
    if regexps['side_to_move'].search( match.group('notation') ).group() == 'b':
      s_to_move = 'Black to move.'
    else:
      s_to_move = 'White to move.'
    html = html.replace(match.group(), s_img + '<br/>' + s_to_move)
  return html

addHook("mungeQA", fen_mungeQA)
