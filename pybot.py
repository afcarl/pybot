#!/usr/bin/env python
##
##  pybot.py
##
##  A LightBot clone for blind students.
##  Works with Python2/3 + Pygame (including Raspberry Pi).
##

import sys
import os.path
import pygame
import socket
try:
    from urllib import urlopen
except ImportError:
    from urllib.request import urlopen

    
def get_server_addr():
    try:
        addr = socket.gethostbyname(socket.gethostname())
    except socket.error:
        return None
    addr = addr.split('.')
    if addr[0] == '127':
        return None
    addr[-1] = '1'
    return '.'.join(addr)

FGCOLOR = (255,255,0)
BGCOLOR = (0,0,255)
HICOLOR = (255,0,0)
GRID = 64
LINE = 80
CSIZE = 20

KEYCODE2SYM = {
    (256,256,300): '00',
    (256,300): '0',
    (257,300): '1',
    (258,300): '2',
    (259,300): '3',
    (260,300): '4',
    (261,300): '5',
    (262,300): '6',
    (263,300): '7',
    (264,300): '8',
    (265,300): '9',
    (266,300): '.',
    (267,300): '/',
    (268,300): '*',
    (269,300): '-',
    (270,300): '+',
    (271,300): 'ENTER',
    (8,): 'BS',
    (9,): 'TAB',
}
# for PC
KEYCODE2SYM.update({
    (48,): '0',
    (49,): '1',
    (50,): '2',
    (51,): '3',
    (52,): '4',
    (53,): '5',
    (54,): '6',
    (55,): '7',
    (56,): '8',
    (57,): '9',
    (273,): '-',  # UP
    (274,): '+',  # DOWN
    (278,): 'BS',  # HOME
    (13,): 'ENTER',
})

SYM2POS = {
    'TAB': (0,0),
    '/': (1,0),
    '*': (2,0),
    '7': (0,1),
    '8': (1,1),
    '9': (2,1),
    '4': (0,2),
    '5': (1,2),
    '6': (2,2),
    '1': (0,3),
    '2': (1,3),
    '3': (2,3),
    '0': (0,4),
    '00': (1,4),
    '.': (2,4),
}

SYM2CMD = {
    '1': 'G',
    '2': 'L',
    '3': 'R',
    '4': 'H1',
    '5': 'J1',
    '6': 'B1',
    '7': 'H2',
    '8': 'J2',
    '9': 'B2',
}

TILE2SOUND = {
    '.': 'tile_empty',
    '@': 'tile_goal',
    '#': 'tile_wall',
    '!': 'tile_bomb',
    '=': 'tile_door',
    '%': 'tile_key',
}

TILE2DIR = {
    'N': (0,-1), 
    'S': (0,1), 
    'E': (1,0), 
    'W': (-1,0), 
}

DIR2SOUND = {
    (0,-1): 'dir_north',
    (0,1): 'dir_south',
    (1,0): 'dir_east',
    (-1,0): 'dir_west',
}

CMD2SOUND = {
    'G': 'cmd_go',
    'L': 'cmd_left',
    'R': 'cmd_right',
    'H1': 'cmd_here1',
    'J1': 'cmd_jump1',
    'B1': 'cmd_branch1',
    'H2': 'cmd_here2',
    'J2': 'cmd_jump2',
    'B2': 'cmd_branch2',
}

SND_OK = 'snd_ok'
SND_NG = 'snd_ng'
SOUNDS = (
    SND_OK,
    SND_NG,
    'mode_editor',
    'mode_runtime',
    'tile_empty',
    'tile_goal',
    'tile_wall',
    'tile_bomb',
    'tile_door',
    'tile_open',
    'tile_key',
    'level_begin',
    'level_end',
    'level_change',
    # voices
    'dir_north',
    'dir_south',
    'dir_east',
    'dir_west',
    'cmd_end',
    'cmd_undo',
    'cmd_go',
    'cmd_left',
    'cmd_right',
    'cmd_here1',
    'cmd_jump1',
    'cmd_branch1',
    'cmd_here2',
    'cmd_jump2',
    'cmd_branch2',
    'num_00',
    'num_01',
    'num_02',
    'num_03',
    'num_04',
    'num_05',
    'num_06',
    'num_07',
    'num_08',
    'num_09',
    'num_10',
    'num_11',
    'num_12',
    'num_13',
    'num_14',
    'num_15',
    'num_16',
    'num_17',
    'num_18',
    'num_19',
    'num_20',
)

class App:

    def __init__(self, surface, font, sounds, baseurls):
        (self.width, self.height) = surface.get_size()
        self.surface = surface
        self.font = font
        self.sounds = sounds
        self.baseurls = baseurls
        self._taskq = []
        self._data0 = None
        self.log('App(%d,%d, baseurls=%r)' % (self.width, self.height, self.baseurls))
        return

    def log(self, *args):
        print(' '.join(args))
        return

    def poll(self):
        data = None
        for url in self.baseurls:
            if url.startswith('//'):
                addr = get_server_addr()
                if addr is None: continue
                url = 'http://%s/%s' % (addr, url[2:])
            self.log('poll: %r' % url)
            if url.startswith('http://'):
                try:
                    index = urlopen(url)
                    if index.getcode() not in (None, 200):
                        self.log('poll: http error: %s' % index.getcode())
                        continue
                    data = index.read()
                    index.close()
                    break
                except IOError as e:
                    self.log('poll: io error: %s' % e)
                    continue
            else:
                # fallback to local files.
                try:
                    index = open(url)
                    data = index.read()
                    index.close()
                    break
                except IOError as e:
                    self.log('poll: io error: %s' % e)
                    continue
        if self._data0 != data:
            try:
                (board, code, codelimit, cmdlimit) = eval(data.strip())
            except Exception as e:
                self.log('poll: invalid data: %r' % e)
                return False
            self._data0 = data
            self.playSound('level_change')
            self.init(board, code, codelimit=codelimit, cmdlimit=cmdlimit)
            return True
        return False

    def init(self, board, code=[], codelimit=None, cmdlimit=None):
        self.log('init')
        self.codelimit = codelimit
        self.cmdlimit = cmdlimit
        self.loadBoard(board)
        self.loadCode(list(code))
        self.initRuntime()
        self.refresh()
        return
        
    def run(self):
        pygame.time.set_timer(pygame.USEREVENT, 33)
        keys = []
        t0 = 0
        while 1:
            e = pygame.event.wait()
            if e.type == pygame.QUIT:
                break
            elif e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_q, pygame.K_ESCAPE, pygame.K_F4):
                    break
                else:
                    t0 = pygame.time.get_ticks()
                    keys.append(e.key)
            elif e.type == pygame.VIDEOEXPOSE:
                self.refresh()
            elif e.type == pygame.USEREVENT:
                t = pygame.time.get_ticks()
                if 50 <= (t-t0):
                    k = KEYCODE2SYM.get(tuple(sorted(keys)))
                    keys = []
                    if k is not None:
                        self.keypress(k)
                        self.refresh()
                self.update()
        return

    def drawText(self, s, x, y, highlight=False):
        if highlight:
            b = self.font.render(s, 0, BGCOLOR, FGCOLOR)
        else:
            b = self.font.render(s, 0, FGCOLOR, BGCOLOR)
        self.surface.blit(b, (x,y))
        return

    def playSound(self, name=None):
        if name is not None:
            self._taskq.append(self.sounds[name])
        else:
            pygame.mixer.stop()
            self._taskq = []
        return

    def addTask(self, task):
        self._taskq.append(task)
        return

    def update(self):
        if self._taskq:
            if not pygame.mixer.get_busy():
                task = self._taskq.pop(0)
                if hasattr(task, 'play'):
                    task.play()
                elif callable(task):
                    task()
        else:
            if self.mode == 'editor':
                self.updateEditor()
            elif self.mode == 'runtime':
                self.updateRuntime()
        return
    
    def keypress(self, k):
        if k == 'BS':
            if self.poll(): return
        assert self._editpos < len(self._code)
        assert self._runpos < len(self._code)
        self.log('keypress: %r' % k)
        self.playSound()
        if self.mode == 'editor':
            self.keypressEditor(k)
        elif self.mode == 'runtime':
            self.keypressRuntime(k)
        return

    def refresh(self):
        self.surface.fill(BGCOLOR)
        self.drawBoard(16, 96)
        if self.mode == 'editor':
            self.drawText('Editor', 16, 0)
            self.drawCode(256, 80, self._editpos, self._curcmd)
        elif self.mode == 'runtime':
            self.drawText('Runtime', 16, 0)
            self.drawCode(256, 80, self._runpos)
        pygame.display.flip()
        return

    def initEditor(self):
        self.log('initEditor')
        self.mode = 'editor'
        self.playSound('mode_editor')
        self._editpos = 0
        self._curcmd = None
        self.resetState()
        self.playCmd(self._code[self._editpos])
        return

    def keypressEditor(self, k):
        if k == 'BS':
            self.initRuntime()
        elif k == 'ENTER':
            if self._curcmd is not None:
                self.playSound(SND_OK)
                self._code[self._editpos] = self._curcmd
                if self.codelimit is None or self._editpos < self.codelimit:
                    self._editpos += 1
                    if len(self._code) <= self._editpos:
                        self._code.append(None)
                    self._curcmd = self._code[self._editpos]
            else:
                self.playSound(SND_NG)
        elif k == '-':
            if 0 < self._editpos:
                self._editpos -= 1
            else:
                self.playSound(SND_NG)
            self._curcmd = self._code[self._editpos]
            self.playNum(self._editpos+1)
            self.playCmd(self._curcmd)
        elif k == '+':
            if self._editpos+1 < len(self._code):
                self._editpos += 1
            else:
                self.playSound(SND_NG)
            self._curcmd = self._code[self._editpos]
            self.playNum(self._editpos+1)
            self.playCmd(self._curcmd)
        elif k in SYM2CMD:
            if self.codelimit is None or self._editpos < self.codelimit:
                cmd = SYM2CMD[k]
                if self.cmdlimit is None or cmd in self.cmdlimit:
                    self._curcmd = cmd
                    self.playCmd(cmd)
            else:
                self.playSound(SND_NG)
        return

    def updateEditor(self):
        return

    def initRuntime(self):
        self.log('initRuntime')
        self.mode = 'runtime'
        self.playSound('mode_runtime')
        self.resetState()
        self._nexttime = 0
        return
        
    def keypressRuntime(self, k):
        if k == 'BS':
            self.initEditor()
        elif k == 'ENTER':
            if self._running:
                self._running = False
            else:
                self.resetState()
                self._running = True
                self._nexttime = 0
                self.playSound('level_begin')
        elif k == '-':
            self._running = False
            if 0 < len(self._history):
                (cmd, state) = self._history.pop(-1)
                self.log('undo: %r' % cmd)
                self.playSound('cmd_undo')
                self.playCmd(cmd)
                self.setState(state)
            else:
                self.playSound(SND_NG)
        elif k == '+':
            self._running = False
            cmd = self._code[self._runpos]
            self.playNum(self._runpos+1)
            self.playCmd(cmd)
            if cmd is not None:
                self.addTask(self.stepCmd)
        else:
            pos = SYM2POS.get(k)
            self.playTile(pos, playEmpty=True)
        return

    def updateRuntime(self):
        if not self._running: return
        t = pygame.time.get_ticks()
        if t < self._nexttime: return
        self._nexttime = t+1000
        cmd = self._code[self._runpos]
        self.playCmd(cmd)
        if cmd is not None:
            self.addTask(self.stepCmd)
        else:
            self._running = False
        self.refresh()
        return

    def stepCmd(self):
        cmd = self._code[self._runpos]
        if cmd is not None:
            self._history.append((cmd, self.getState()))
            self._runpos += 1
        self.execCmd(cmd)
        return

    def clearLevel(self):
        self._running = False
        self.playSound('level_end')
        return

    def loadBoard(self, data):
        self.log('loadBoard: %r' % data)
        self._board = {}
        self._startpos = None
        self._startdir = None
        for (y,row) in enumerate(data.split('/')):
            for (x,c) in enumerate(row):
                if c == ' ': continue
                if c in TILE2DIR:
                    self._startpos = (x,y)
                    self._startdir = TILE2DIR[c]
                    c = '.'
                self._board[(x,y)] = c
        assert self._startpos is not None
        assert self._startdir is not None
        return

    def loadCode(self, code):
        self.log('loadCode: %r' % code)
        self._editpos = 0
        self._code = list(code)+[None]
        return

    def jumpTo(self, label):
        self.log('jumpTo: %r' % label)
        for (i,c) in enumerate(self._code):
            if label == c:
                self._runpos = i
                break
        return

    def resetState(self):
        self.log('resetState')
        self._robpos = self._startpos
        self._robdir = self._startdir
        self._haskey = False
        self._runpos = 0
        self._history = []
        self._running = False
        return

    def getState(self):
        return (self._robpos, self._robdir, self._haskey, self._runpos)

    def setState(self, state):
        (self._robpos, self._robdir, self._haskey, self._runpos) = state
        return

    def moveTo(self, pos):
        self.log('moveTo: %r' % (pos,))
        assert pos in self._board
        self.playTile(pos)
        c = self._board[pos]
        if c == '@':
            self._robpos = pos
            self.clearLevel()
        elif c == '#':
            pass
        elif c == '!':
            self.resetState()
        elif c == '=':
            if self._haskey:
                self._robpos = pos
        elif c == '%' and not self._haskey:
            self._haskey = True
            self._robpos = pos
        else:
            self._robpos = pos
        return

    def execCmd(self, cmd):
        self.log('execCmd: %r' % cmd)
        if cmd == 'L':
            (vx,vy) = self._robdir
            self._robdir = (vy,-vx)
            self.playSound(SND_OK)
        elif cmd == 'R':
            (vx,vy) = self._robdir
            self._robdir = (-vy,vx)
            self.playSound(SND_OK)
        elif cmd == 'G':
            (vx,vy) = self._robdir
            (x,y) = self._robpos
            x += vx
            y += vy
            if (x,y) in self._board:
                self.moveTo((x,y))
            else:
                self.playSound(SND_NG)
        elif cmd == 'J1':
            self.jumpTo('H1')
        elif cmd == 'J2':
            self.jumpTo('H2')
        elif cmd == 'B1':
            if not self._haskey:
                self.jumpTo('H1')
        elif cmd == 'B2':
            if not self._haskey:
                self.jumpTo('H2')
        self.refresh()
        return

    def playNum(self, n):
        if 0 <= n and n <= 20:
            self.playSound('num_%02d' % n)
        return

    def playCmd(self, cmd):
        if cmd is None:
            self.playSound('cmd_end')
        else:
            self.playSound(CMD2SOUND[cmd])
        return

    def playDir(self, d):
        self.playSound(DIR2SOUND[d])
        return

    def playTile(self, pos, playEmpty=False):
        if pos == self._robpos:
            self.playDir(self._robdir)
        else:
            try:
                c = self._board[pos]
                if c == '=' and self._haskey:
                    self.playSound('tile_open')
                elif c == '.':
                    if playEmpty:
                        self.playSound(TILE2SOUND[c])
                    else:
                        self.playSound(SND_OK)
                else:
                    self.playSound(TILE2SOUND[c])
            except KeyError:
                self.playSound(SND_NG)
        return

    def drawCode(self, x0, y0, start, curcmd=None, nlines=5):
        for y in range(nlines):
            i = start+y
            if i < 0 or len(self._code) <= i: continue
            if i == start and curcmd is not None:
                cmd = curcmd
            else:
                cmd = self._code[i]
            if cmd is None:
                cmd = '_'
            line = '%02d: %s' % (i+1, cmd)
            self.drawText(line, x0, y*LINE+y0, i == start)
        return

    def drawBoard(self, x0, y0):
        G = GRID
        H = GRID//2
        for ((x,y),c) in self._board.items():
            x = x*G+x0
            y = y*G+y0
            rect = (x+4, y+4, G-8, G-8)
            pygame.draw.rect(self.surface, FGCOLOR, rect, 4)
            if c == '@':
                rect = (x+12, y+12, G-24, G-24)
                pygame.draw.rect(self.surface, FGCOLOR, rect, 4)
                rect = (x+20, y+20, G-40, G-40)
                pygame.draw.rect(self.surface, FGCOLOR, rect, 4)
            elif c == '#':
                rect = (x+8, y+8, G-16, G-16)
                self.surface.fill(FGCOLOR, rect)
            elif c == '!':
                pygame.draw.line(self.surface, FGCOLOR, (x+8,y+8),
                                 (x+G-12, y+G-12), 4)
                pygame.draw.line(self.surface, FGCOLOR, (x+8,y+G-12),
                                 (x+G-12, y+8), 4)
                pygame.draw.circle(self.surface, FGCOLOR, (x+H,y+H), 16)
            elif c == '=':
                if self._haskey:
                    rect = (x+12, y+12, G-24, G-24)
                    pygame.draw.rect(self.surface, FGCOLOR, rect, 4)
                else:
                    pygame.draw.line(self.surface, FGCOLOR, (x+8,y+H-8),
                                     (x+G-12, y+H-8), 4)
                    pygame.draw.line(self.surface, FGCOLOR, (x+8,y+H+8),
                                     (x+G-12, y+H+8), 4)
                    pygame.draw.line(self.surface, FGCOLOR, (x+H-8,y+8),
                                     (x+H-8, y+G-12), 4)
                    pygame.draw.line(self.surface, FGCOLOR, (x+H+8,y+8),
                                     (x+H+8, y+G-12), 4)
            elif c == '%':
                if not self._haskey:
                    pygame.draw.circle(self.surface, FGCOLOR, (x+H-8,y+H+8), 12, 4)
                    pygame.draw.line(self.surface, FGCOLOR, (x+H,y+H),
                                     (x+G-16, y+16), 4)
                    pygame.draw.line(self.surface, FGCOLOR, (x+G-16, y+16),
                                     (x+G-8, y+24), 4)
                    pygame.draw.line(self.surface, FGCOLOR, (x+G-24, y+24),
                                     (x+G-16, y+32), 4)
        (x,y) = self._robpos
        (vx,vy) = self._robdir
        x = x*G+H+x0
        y = y*G+H+y0
        pts = [ (dx*CSIZE+x, dy*CSIZE+y) for (dx,dy)
                in ((-vy-vx,vx-vy), (vx,vy), (vy-vx,-vx-vy)) ]
        pygame.draw.polygon(self.surface, FGCOLOR, pts)
        return

    
def main(argv):
    import getopt
    def usage():
        print('usage: %s [-d] [-f] [-F fonts] [-S sounds] [url ...]' % argv[0])
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 'dfF:S:')
    except getopt.GetoptError:
        return usage()
    debug = 0
    mode = (640,480)
    flags = 0
    fontpath = './fonts/VeraMono.ttf'
    sounddir = './sounds/'
    for (k, v) in opts:
        if k == '-d': debug += 1
        elif k == '-f': flags = pygame.FULLSCREEN
        elif k == '-F': fontpath = v
        elif k == '-S': sounddir = v
    #
    pygame.mixer.pre_init(22050, -16, 1)
    pygame.init()
    modes = pygame.display.list_modes()
    if mode not in modes:
        mode = modes[0]
    pygame.display.set_mode(mode, flags)
    pygame.mouse.set_visible(0)
    pygame.key.set_repeat()
    font = pygame.font.Font(fontpath, 64)
    sounds = {}
    for name in SOUNDS:
        path = os.path.join(sounddir, name+'.wav')
        sounds[name] = pygame.mixer.Sound(path)
    #
    app = App(pygame.display.get_surface(), font, sounds, args)
    app.init('@#./.../#=!/..%/E..')
    app.poll()
    return app.run()

if __name__ == '__main__': sys.exit(main(sys.argv))
