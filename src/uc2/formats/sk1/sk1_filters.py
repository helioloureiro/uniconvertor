# -*- coding: utf-8 -*-
#
#  Copyleft  (L) 2021 by Helio Loureiro
#  Copyright (C) 2013 by Ihor E. Novikov
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License
#  as published by the Free Software Foundation, either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>..

import logging

from uc2 import uc2const
from uc2.formats.generic_filters import AbstractLoader, AbstractSaver
from uc2.formats.sk1 import sk1_const
from uc2.formats.sk1.model import SK1Document, SK1Layout, SK1Grid, SK1Pages, \
    SK1Page, SK1Layer, SK1MasterLayer, SK1GuideLayer, SK1Guide, SK1Group, \
    SK1MaskGroup, Rectangle, Ellipse, PolyBezier, SK1Text, SK1BitmapData, \
    SK1Image, \
    MultiGradient, EmptyPattern, SolidPattern, LinearGradient, RadialGradient, \
    ConicalGradient, HatchingPattern, ImageTilePattern, Style, Trafo, Point

LOG = logging.getLogger(__name__)


class SK1Loader(AbstractLoader):
    name = 'SK1_Loader'

    paths = []
    options = {}
    pages = None

    string = ''
    line = ''
    active_page = None
    active_layer = None
    parent_stack = []
    obj_style = []

    style_obj = None
    style_dict = {}
    pattern = None
    gradient = None

    def do_load(self):
        self.model = None
        self.paths = []
        self.options = {}
        self.parent_stack = []
        self.obj_style = []
        self.style_dict = {}
        self.fileptr.readline()
        self.style_obj = Style()
        while True:
            self.line = self.fileptr.readline()
            if not self.line:
                break
            self.line = self.line.rstrip('\r\n')

            self.check_loading()

            if self.line:
                try:
                    code = compile('self.' + self.line, '<string>', 'exec')
                    exec(code)
                except Exception as e:
                    LOG.warn('Parsing error in "%s"', self.line)
                    LOG.warn('Error traceback: %s', e)

    def set_style(self, obj):
        obj.properties = self.style_obj
        self.style_obj = Style()

    def add_object(self, obj, parent=''):
        if self.model is None:
            self.model = obj
        else:
            if not parent:
                if self.parent_stack:
                    parent = self.parent_stack[-1]
                else:
                    parent = self.active_layer
            obj.parent = parent
            obj.config = self.config
            parent.childs.append(obj)

    # ---PROPERTIES
    def gl(self, colors):
        self.gradient = MultiGradient(colors)

    def pe(self):
        self.pattern = EmptyPattern

    def ps(self, color):
        self.pattern = SolidPattern(color)

    def pgl(self, dx, dy, border=0):
        if not self.gradient:
            self.gradient = MultiGradient()
        self.pattern = LinearGradient(self.gradient, Point(dx, dy), border)

    def pgr(self, dx, dy, border=0):
        if not self.gradient:
            self.gradient = MultiGradient()
        self.pattern = RadialGradient(self.gradient, Point(dx, dy), border)

    def pgc(self, cx, cy, dx, dy):
        if not self.gradient:
            self.gradient = MultiGradient()
        self.pattern = ConicalGradient(self.gradient, Point(cx, cy),
                                       Point(dx, dy))

    def phs(self, color, background, dx, dy, dist, width):
        self.pattern = HatchingPattern(color, background, Point(dx, dy), dist,
                                       width)

    def pit(self, obj_id, trafo):
        trafo = Trafo(*trafo)
        if obj_id in self.presenter.resources:
            image = self.presenter.resources[obj_id]
            self.pattern = ImageTilePattern(image, trafo)

    def fp(self, color=None):
        if color is None:
            self.style_obj.fill_pattern = self.pattern
        else:
            self.style_obj.fill_pattern = SolidPattern(color)

    def fe(self):
        self.style_obj.fill_pattern = EmptyPattern

    def ft(self, val):
        self.style_obj.fill_transform = val

    def lp(self, color=None):
        if color is None:
            self.style_obj.line_pattern = self.pattern
        else:
            self.style_obj.line_pattern = SolidPattern(color)

    def le(self):
        self.style_obj.line_pattern = EmptyPattern

    def lw(self, width):
        self.style_obj.line_width = width

    def lc(self, cap):
        if not 1 <= cap <= 3:
            cap = 1
        self.style_obj.line_cap = cap

    def lj(self, join):
        self.style_obj.line_join = join

    def ld(self, dashes):
        self.style_obj.line_dashes = dashes

    def la1(self, args=None):
        self.style_obj.line_arrow1 = args

    def la2(self, args=None):
        self.style_obj.line_arrow2 = args

    def Fs(self, size):
        self.style_obj.font_size = size

    def Fn(self, name, face=None):
        self.style_obj.font = name
        self.style_obj.font_face = face

    def dstyle(self, name=''):
        if name:
            self.style_obj.name = name
            self.model.styles[name] = self.style_obj
            self.style_obj = Style()

    def style(self, name=''):
        if name and name in self.model.styles:
            self.style_obj = self.model.styles[name].copy()

    def use_style(self, name=''):
        self.style(name)

    # ---STRUCTURAL ELEMENTS
    def document(self, *args):
        self.add_object(SK1Document(self.config))

    def layout(self, *args):
        if len(args) > 2:
            pformat = args[0]
            size = args[1]
            orientation = args[2]
        else:
            if not isinstance(args[0], tuple):
                pformat = args[0]
                orientation = args[1]
                if pformat not in uc2const.PAGE_FORMAT_NAMES:
                    pformat = 'A4'
                size = uc2const.PAGE_FORMATS[pformat]
            else:
                pformat = ''
                size = args[0]
                orientation = args[1]
        obj = SK1Layout(pformat, size, orientation)
        self.add_object(obj, self.model)
        self.model.layout = obj

    def grid(self, grid, visibility, grid_color, layer_name):
        obj = SK1Grid(grid, visibility, grid_color, layer_name)
        self.add_object(obj, self.model)
        self.model.grid = obj

    def add_pages(self, *args):
        self.pages = SK1Pages()
        self.add_object(self.pages, self.model)
        self.model.pages = self.pages

    def page(self, name='', pformat='', size='', orientation=0):
        if self.pages is None:
            self.add_pages()
        if not pformat and not size:
            pformat = self.model.layout.format
            size = () + self.model.layout.size
            orientation = self.model.layout.orientation
        page = SK1Page(name, pformat, size, orientation)
        self.active_page = page
        self.active_layer = None
        self.parent_stack = []
        self.add_object(page, self.pages)

    def layer(self, name, p1, p2, p3, p4, layer_color):
        if self.active_page is None:
            self.page()
        layer = SK1Layer(name, p1, p2, p3, p4, layer_color)
        self.active_layer = layer
        self.add_object(layer, self.active_page)

    def masterlayer(self, name, p1, p2, p3, p4, layer_color):
        mlayer = SK1MasterLayer(name, p1, p2, p3, p4, layer_color)
        self.active_layer = mlayer
        self.add_object(mlayer, self.model)
        self.model.masterlayer = mlayer

    def guidelayer(self, name, p1, p2, p3, p4, layer_color):
        glayer = SK1GuideLayer(name, p1, p2, p3, p4, layer_color)
        self.active_layer = glayer
        self.add_object(glayer, self.model)
        self.model.guidelayer = glayer

    def guide(self, point, orientation):
        self.add_object(SK1Guide(point, orientation))

    # ---GROUPS
    def G(self):
        group = SK1Group()
        self.add_object(group)
        self.parent_stack.append(group)

    def G_(self):
        self.parent_stack = self.parent_stack[:-1]

    def M(self):
        mgroup = SK1MaskGroup()
        self.add_object(mgroup)
        self.parent_stack.append(mgroup)

    def M_(self):
        self.parent_stack = self.parent_stack[:-1]

    def B(self):
        group = SK1Group()
        self.string = group.string
        self.line = ''
        self.add_object(group)
        self.parent_stack.append(group)

    def Bi(self, *args):
        self.string = ''

    def B_(self):
        self.parent_stack = self.parent_stack[:-1]

    def PT(self):
        group = SK1Group()
        self.string = group.string
        self.line = ''
        self.add_object(group)
        self.parent_stack.append(group)

    def pt(self, *args):
        self.string = ''

    def PT_(self):
        self.parent_stack = self.parent_stack[:-1]

    def PC(self, *args):
        group = SK1Group()
        self.string = group.string
        self.line = ''
        self.add_object(group)
        self.parent_stack.append(group)

    def PC_(self):
        self.parent_stack = self.parent_stack[:-1]

    # ---PRIMITIVES
    def r(self, m11, m12, m21, m22, dx, dy, radius1=0, radius2=0):
        trafo = Trafo(m11, m12, m21, m22, dx, dy)
        obj = Rectangle(trafo, radius1, radius2)
        self.set_style(obj)
        self.add_object(obj)

    def e(self, m11, m12, m21, m22, dx, dy, start_angle=0.0, end_angle=0.0,
          arc_type=sk1_const.ArcPieSlice):
        trafo = Trafo(m11, m12, m21, m22, dx, dy)
        obj = Ellipse(trafo, start_angle, end_angle, arc_type)
        self.set_style(obj)
        self.add_object(obj)

    def b(self):
        self.paths = [[None, [], sk1_const.CURVE_OPENED]]
        obj = PolyBezier(paths_list=self.paths)
        self.set_style(obj)
        self.add_object(obj)

    def bs(self, x, y, cont):
        point = [x, y]
        path = self.paths[-1]
        points = path[1]
        if path[0] is None:
            path[0] = point
        else:
            points.append(point)

    def bc(self, x1, y1, x2, y2, x3, y3, cont):
        point = [[x1, y1], [x2, y2], [x3, y3], cont]
        path = self.paths[-1]
        points = path[1]
        if path[0] is None:
            path[0] = point[0]
        else:
            points.append(point)

    def bn(self):
        self.paths.append([None, [], sk1_const.CURVE_OPENED])

    def bC(self):
        self.paths[-1][2] = sk1_const.CURVE_CLOSED

    def txt(self, text, trafo, horiz_align, vert_align, chargap, wordgap,
            linegap):
        if not text:
            return
        if isinstance(text, int):
            lines = text
            text = ''
            for item in range(lines):
                text += self.fileptr.readline()
            text = text[:-1]
        else:
            text = self._decode_text(text)
        obj = SK1Text(text, trafo, horiz_align, vert_align, chargap, wordgap,
                      linegap)
        self.set_style(obj)
        self.add_object(obj)

    def _decode_text(self, text):
       # not exactly sure what this is supposed to do 
       # it seems some odd code to... translate charset from utf-8?
        if sys.getfilesystemencoding() == 'utf-8':
            return text
        return text.encode('latin-1').decode('utf-8')

    def bm(self, obj_id):
        bmd_obj = SK1BitmapData(obj_id)
        self.add_object(bmd_obj)
        try:
            bmd_obj.read_data(self.fileptr)
        except Exception as e:
            LOG.error('Error reading bitmap %s', e)
        self.presenter.resources[obj_id] = bmd_obj.raw_image

    def im(self, trafo, obj_id):
        if len(trafo) == 2:
            trafo = (1.0, 0.0, 0.0, 1.0) + trafo
        trafo = Trafo(*trafo)
        image = None
        if obj_id in self.presenter.resources:
            image = self.presenter.resources[obj_id]
        self.add_object(SK1Image(trafo, obj_id, image))

    def eps(self, *args):
        self.string = ''


class SK1Saver(AbstractSaver):
    name = 'SK1_Saver'

    def do_save(self):
        self.model.write_content(self.fileptr)
