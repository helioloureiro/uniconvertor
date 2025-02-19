# -*- coding: utf-8 -*-
#
#  Copyleft  (L) 2021 by Helio Loureiro
#  Copyright (C) 2011-2017 by Ihor E. Novikov
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
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import copy
from copy import deepcopy

from . import libcms

from uc2 import uc2const
from uc2.uc2const import COLOR_RGB, COLOR_CMYK, COLOR_LAB, COLOR_GRAY, \
    COLOR_SPOT, COLOR_DISPLAY, COLOR_REG
from uc2.uc2const import IMAGE_MONO, IMAGE_GRAY, IMAGE_RGB, IMAGE_CMYK, \
    IMAGE_LAB, IMAGE_TO_COLOR
from uc2.utils import fsutils

CS = [COLOR_RGB, COLOR_CMYK, COLOR_LAB, COLOR_GRAY]


def get_registration_black():
    return [COLOR_SPOT, [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0]], 1.0, COLOR_REG]


def color_to_spot(color):
    if not color:
        return get_registration_black()
    if color[0] == COLOR_SPOT:
        return deepcopy(color)
    rgb = []
    cmyk = []
    name = ''
    if color[0] == COLOR_RGB:
        rgb = deepcopy(color[1])
    elif color[0] == COLOR_CMYK:
        cmyk = deepcopy(color[1])
    elif color[0] == COLOR_GRAY:
        cmyk = gray_to_cmyk(color[1])
    if color[3]:
        name += color[3]
    return [COLOR_SPOT, [rgb, cmyk], color[2], name]


def val_100(vals):
    return [int(round(100 * x)) for x in vals]


def val_255(vals):
    return [int(round(255 * x)) for x in vals]


def val_255_to_dec(vals):
    return [x / 255.0 for x in vals]


def val_100_to_dec(vals):
    return [x / 100.0 for x in vals]


def mix_vals(val1, val2, coef=0.5):
    if val1 < val2:
        return val1 + (val2 - val1) * coef
    else:
        return val1 - (val1 - val2) * coef


def mix_lists(vals1, vals2, coef=0.5):
    if not len(vals1) == len(vals2):
        return None
    ret = []
    index = 0
    for val1 in vals1:
        val2 = vals2[index]
        ret.append(mix_vals(val1, val2, coef))
        index += 1
    return ret


def rgb_to_hexcolor(color):
    """Converts list of RGB float values to hex color string.
    For example: [1.0, 0.0, 1.0] => #ff00ff
    """
    return '#%02x%02x%02x' % tuple(int(round(255 * x)) for x in color)


def rgba_to_hexcolor(color):
    """Converts list of RGBA float values to hex color string.
    For example: [1.0, 0.0, 1.0, 1.0] => #ff00ffff
    """
    return '#%02x%02x%02x%02x' % tuple(int(round(255 * x)) for x in color)


def cmyk_to_hexcolor(color):
    return rgba_to_hexcolor(color)


def hexcolor_to_rgb(hexcolor):
    """Converts hex color string as a list of float values.
    For example: #ff00ff => [1.0, 0.0, 1.0]
    """
    if len(hexcolor) == 4:
        vals = (hexcolor[1] * 2, hexcolor[2] * 2, hexcolor[3] * 2)
    else:
        vals = (hexcolor[1:3], hexcolor[3:5], hexcolor[5:])
    return [int(x, 0x10) / 255.0 for x in vals]


def hexcolor_to_rgba(hexcolor):
    """Converts hex color string as a list of float values.
    For example: #ff00ffff => [1.0, 0.0, 1.0, 1.0]
    """
    vals = ('00', '00', '00', 'ff')
    if len(hexcolor) == 7:
        vals = (hexcolor[1:3], hexcolor[3:5], hexcolor[5:], 'ff')
    elif len(hexcolor) == 9:
        vals = (hexcolor[1:3], hexcolor[3:5], hexcolor[5:7], hexcolor[7:])
    return [int(x, 0x10) / 255.0 for x in vals]


def hexcolor_to_cmyk(hexcolor):
    return hexcolor_to_rgba(hexcolor)


def gdk_hexcolor_to_rgb(hexcolor):
    """ Converts hex color string as a list of float values.
    For example: #ffff0000ffff => [1.0, 0.0, 1.0]
    """
    vals = (hexcolor[1:5], hexcolor[5:6], hexcolor[9:])
    return [int(x, 0x10) / 65535.0 for x in vals]


def rgb_to_gdk_hexcolor(color):
    """Converts hex color string as a list of float values.
    For example: #ffff0000ffff => [1.0, 0.0, 1.0]
    """
    return '#%04x%04x%04x' % tuple(x * 65535.0 for x in color)


def cmyk_to_rgb(color):
    """Converts list of CMYK values to RGB.
    """
    c, m, y, k = color
    return [round(1.0 - min(1.0, x + k), 3) for x in (c, m, y)]


def rgb_to_cmyk(color):
    """Converts list of RGB values to CMYK.
    """
    r, g, b = color
    c = 1.0 - r
    m = 1.0 - g
    y = 1.0 - b
    k = min(c, m, y)
    return [c - k, m - k, y - k, k]


def gray_to_cmyk(color):
    """Converts Gray value to CMYK.
    """
    k = 1.0 - color[0]
    c = m = y = 0.0
    return [c, m, y, k]


def gray_to_rgb(color):
    """Converts Gray value to RGB.
    """
    r = g = b = color[0]
    return [r, g, b]


def rgb_to_gray(color):
    """Converts RGB value to Gray.
    """
    r, g, b = color
    val = (r + g + b) / 3.0
    return [val, ]


def linear_to_rgb(c):
    if c > 0.0031308:
        return pow(c, 1.0 / 2.4) * 1.055 - 0.055
    return c * 12.92


def lab_to_rgb(color):
    """Converts CIE-L*ab value to RGB.
    """
    L, a, b = color
    # L: 0..100
    # a:  -128..127
    # b:  -128..127
    L = L * 100.0
    a = a * 255.0 - 128.0
    b = b * 255.0 - 128.0

    # Lab -> normalized XYZ (X,Y,Z are all in 0...1)
    Y = L * (1.0 / 116.0) + 16.0 / 116.0
    X = a * (1.0 / 500.0) + Y
    Z = b * (-1.0 / 200.0) + Y

    if X > 6.0 / 29.0:
        X = X * X * X
    else:
        X = X * (108.0 / 841.0) - 432.0 / 24389.0
    if L > 8.0:
        Y = Y * Y * Y
    else:
        Y = L * (27.0 / 24389.0)
    if Z > 6.0 / 29.0:
        Z = Z * Z * Z
    else:
        Z = Z * (108.0 / 841.0) - 432.0 / 24389.0

    # normalized XYZ -> linear sRGB (in 0...1)
    R = X * (1219569.0 / 395920.0) + Y * (-608687.0 / 395920.0) + Z * (
            -107481.0 / 197960.0)
    G = X * (-80960619.0 / 87888100.0) + Y * (82435961.0 / 43944050.0) + Z * (
            3976797.0 / 87888100.0)
    B = X * (93813.0 / 1774030.0) + Y * (-180961.0 / 887015.0) + Z * (
            107481.0 / 93370.0)

    # linear sRGB -> gamma-compressed sRGB (in 0...1)
    r = round(linear_to_rgb(R), 3)
    g = round(linear_to_rgb(G), 3)
    b = round(linear_to_rgb(B), 3)
    return [r, g, b]


def xyz_to_lab(c):
    if c > 216.0 / 24389.0:
        return pow(c, 1.0 / 3.0)
    return c * (841.0 / 108.0) + (4.0 / 29.0)


def rgb_to_linear(c):
    if c > (0.0031308 * 12.92):
        return pow(c * (1.0 / 1.055) + (0.055 / 1.055), 2.4)
    return c * (1.0 / 12.92)


def rgb_to_lab(color):
    R, G, B = color

    # RGB -> linear sRGB
    R = rgb_to_linear(R)
    G = rgb_to_linear(G)
    B = rgb_to_linear(B)

    # linear sRGB -> normalized XYZ (X,Y,Z are all in 0...1)
    X = xyz_to_lab(
        R * (10135552.0 / 23359437.0) + G * (8788810.0 / 23359437.0) + B * (
                4435075.0 / 23359437.0))
    Y = xyz_to_lab(
        R * (871024.0 / 4096299.0) + G * (8788810.0 / 12288897.0) + B * (
                887015.0 / 12288897.0))
    Z = xyz_to_lab(
        R * (158368.0 / 8920923.0) + G * (8788810.0 / 80288307.0) + B * (
                70074185.0 / 80288307.0))

    # normalized XYZ -> Lab
    L = round((Y * 116.0 - 16.0) / 100.0, 3)
    a = round(((X - Y) * 500.0 + 128.0) / 255.0, 3)
    b = round(((Y - Z) * 200.0 + 128.0) / 255.0, 3)
    return [L, a, b]


def do_simple_transform(color, cs_in, cs_out):
    """
    Emulates color management library transformation
    """
    if cs_in == cs_out:
        return copy.copy(color)
    if cs_in == COLOR_RGB:
        if cs_out == COLOR_CMYK:
            return rgb_to_cmyk(color)
        elif cs_out == COLOR_GRAY:
            return rgb_to_gray(color)
        elif cs_out == COLOR_LAB:
            return rgb_to_lab(color)
    elif cs_in == COLOR_CMYK:
        if cs_out == COLOR_RGB:
            return cmyk_to_rgb(color)
        elif cs_out == COLOR_GRAY:
            return rgb_to_gray(cmyk_to_rgb(color))
        elif cs_out == COLOR_LAB:
            return rgb_to_lab(cmyk_to_rgb(color))
    elif cs_in == COLOR_GRAY:
        if cs_out == COLOR_RGB:
            return gray_to_rgb(color)
        elif cs_out == COLOR_CMYK:
            return gray_to_cmyk(color)
        elif cs_out == COLOR_LAB:
            return rgb_to_lab(gray_to_rgb(color))
    elif cs_in == COLOR_LAB:
        if cs_out == COLOR_RGB:
            return lab_to_rgb(color)
        elif cs_out == COLOR_CMYK:
            return rgb_to_cmyk(lab_to_rgb(color))
        elif cs_out == COLOR_GRAY:
            return rgb_to_gray(lab_to_rgb(color))


def colorb(color=None, cmyk=False):
    """
    Emulates COLORB object from python-lcms.
    Actually function returns regular 4-member list.
    """
    if color is None:
        return [0, 0, 0, 0]
    if color[0] == uc2const.COLOR_SPOT:
        if cmyk:
            values = color[1][1]
        else:
            values = color[1][0]
    else:
        values = color[1]

    result = []
    if color[0] == uc2const.COLOR_LAB:
        result.append(int(round(values[0] * 100)))
        result.append(int(round(values[1] * 255)))
        result.append(int(round(values[2] * 255)))
    else:
        for value in values:
            result.append(int(round(value * 255)))

    if len(result) == 1:
        result += [0, 0, 0]
    elif len(result) == 3:
        result += [0]
    return result


def decode_colorb(colorb, color_type):
    """
    Decodes colorb list into generic color values.
    """
    result = []
    if color_type == uc2const.COLOR_CMYK:
        values = colorb
    elif color_type == uc2const.COLOR_GRAY:
        values = [colorb[0], ]
    else:
        values = colorb[:3]

    if color_type == uc2const.COLOR_LAB:
        result.append(values[0] / 100.0)
        result.append(values[1] / 255.0)
        result.append(values[2] / 255.0)
    else:
        for value in values:
            result.append(value / 255.0)
    return result


def verbose_color(color):
    if not color:
        return 'No color'
    cs = color[0]
    val = [] + color[1]
    alpha = color[2]
    if cs == COLOR_CMYK:
        c, m, y, k = val_100(val)
        ret = 'C-%d%% M-%d%% Y-%d%% K-%d%%' % (c, m, y, k)
        if alpha < 1.0:
            ret += ' A-%d%%' % val_100([alpha, ])[0]
    elif cs == COLOR_RGB:
        r, g, b = val_255(val)
        ret = 'R-%d G-%d B-%d' % (r, g, b)
        if alpha < 1.0:
            ret += ' A-%d' % val_255([alpha, ])[0]
    elif cs == COLOR_GRAY:
        g = val_255(val)[0]
        ret = 'Gray-%d' % g
        if alpha < 1.0:
            ret += ' Alpha-%d' % val_255([alpha, ])[0]
    elif cs == COLOR_LAB:
        l, a, b = val
        l = l * 100.0
        a = a * 255.0 - 128.0
        b = b * 255.0 - 128.0
        ret = 'L %d a %d b %d' % (l, a, b)
        if alpha < 1.0:
            ret += ' Alpha-%d' % val_255([alpha, ])[0]
    elif cs == COLOR_SPOT:
        ret = color[3]
    else:
        return '???'

    return ret


def get_profile_name(filepath):
    """Returns profile name.
    If file is not suitable profile or doesn't exist
    returns None.
    """
    try:
        filepath = fsutils.get_sys_path(filepath)
        profile = libcms.cms_open_profile_from_file(filepath)
        ret = libcms.cms_get_profile_name(profile)
    except Exception:
        ret = None
    return ret


def get_profile_info(filepath):
    """Returns profile info.
    If file is not suitable profile or doesn't exist
    returns None.
    """
    try:
        filepath = fsutils.get_sys_path(filepath)
        profile = libcms.cms_open_profile_from_file(filepath)
        ret = libcms.cms_get_profile_info(profile)
    except Exception:
        ret = None
    return ret


def get_profile_descr(filepath):
    """Returns profile description tuple (name, copyright, info).
    If file is not suitable profile or doesn't exist
    returns None.
    """
    try:
        filepath = fsutils.get_sys_path(filepath)
        profile = libcms.cms_open_profile_from_file(filepath)
        ret = (libcms.cms_get_profile_name(profile),)
        ret += (libcms.cms_get_profile_copyright(profile),)
        ret += (libcms.cms_get_profile_info(profile),)
    except Exception:
        ret = ('', '', '')
    return ret


class ColorManager(object):
    """The class provides abstract color manager.
    On CM object instantiation default built-in profiles
    are used to create internal stuff.
    """

    handles = None
    transforms = None
    proof_transforms = None

    use_cms = True
    use_display_profile = False
    proofing = False
    gamutcheck = False
    alarm_codes = (0.0, 1.0, 1.0)
    proof_for_spot = False

    rgb_intent = uc2const.INTENT_RELATIVE_COLORIMETRIC
    cmyk_intent = uc2const.INTENT_PERCEPTUAL
    flags = uc2const.cmsFLAGS_NOTPRECALC

    def __init__(self):
        self.update()

    def update(self):
        """
        Sets color profile handles using built-in profiles
        """
        self.handles = {}
        self.clear_transforms()
        for item in CS:
            self.handles[item] = libcms.cms_create_default_profile(item)

    def clear_transforms(self):
        self.transforms = {}
        self.proof_transforms = {}

    def get_transform(self, cs_in, cs_out):
        """
        Returns requested color transform using self.transforms dict.
        If requested transform is not initialized yet, creates it.
        """
        tr_type = cs_in + cs_out
        intent = self.rgb_intent
        if cs_out == COLOR_CMYK:
            intent = self.cmyk_intent
        if tr_type not in self.transforms:
            handle_in = self.handles[cs_in]
            handle_out = self.handles[cs_out]
            if cs_out == COLOR_DISPLAY:
                cs_out = COLOR_RGB
            tr = libcms.cms_create_transform(handle_in, cs_in,
                                             handle_out, cs_out,
                                             intent, self.flags)
            self.transforms[tr_type] = tr
        return self.transforms[tr_type]

    def get_proof_transform(self, cs_in):
        """
        Returns requested proof transform using self.proof_transforms dict.
        If requested transform is not initialized yet, creates it.
        """
        tr_type = cs_in
        if tr_type not in self.proof_transforms:
            handle_in = self.handles[cs_in]
            if self.use_display_profile and COLOR_DISPLAY in self.handles:
                handle_out = self.handles[COLOR_DISPLAY]
            else:
                handle_out = self.handles[COLOR_RGB]
            handle_proof = self.handles[COLOR_CMYK]
            tr = libcms.cms_create_proofing_transform(handle_in, cs_in,
                                                      handle_out, COLOR_RGB,
                                                      handle_proof,
                                                      self.cmyk_intent,
                                                      self.rgb_intent,
                                                      self.flags)
            self.proof_transforms[tr_type] = tr
        return self.proof_transforms[tr_type]

    def do_transform(self, color, cs_in, cs_out):
        """
        Converts color between colorspaces.
        Returns list of color values.
        """
        if not self.use_cms:
            return do_simple_transform(color[1], cs_in, cs_out)
        in_color = colorb(color)
        out_color = colorb()
        transform = self.get_transform(cs_in, cs_out)
        libcms.cms_do_transform(transform, in_color, out_color)
        return decode_colorb(out_color, cs_out)

    def do_bitmap_transform(self, img, mode, cs_out=None):
        """
        Does image proof transform.
        Returns new image instance.
        """
        if not self.use_cms and not img.mode == IMAGE_LAB:
            return img.convert(mode)
        cs_in = IMAGE_TO_COLOR[img.mode]
        if not cs_out:
            cs_out = IMAGE_TO_COLOR[mode]
        transform = self.get_transform(cs_in, cs_out)
        return libcms.cms_do_bitmap_transform(transform, img, img.mode, mode)

    def do_proof_transform(self, color, cs_in):
        """
        Does color proof transform.
        Returns list of color values.
        """
        in_color = colorb(color)
        out_color = colorb()
        transform = self.get_proof_transform(cs_in)
        libcms.cms_do_transform(transform, in_color, out_color)
        return decode_colorb(out_color, COLOR_RGB)

    def do_proof_bitmap_transform(self, img):
        """
        Does image proof transform.
        Returns new image instance.
        """
        cs_in = IMAGE_TO_COLOR[img.mode]
        mode = IMAGE_RGB
        transform = self.get_proof_transform(cs_in)
        return libcms.cms_do_bitmap_transform(transform, img, img.mode, mode)

    # Color management API
    def get_rgb_color(self, color):
        """
        Convert color into RGB color.
        Stores alpha channel and color name.
        """
        if color[0] == COLOR_RGB:
            return deepcopy(color)
        if color[0] == COLOR_SPOT:
            if color[1][0]:
                return [COLOR_RGB, [] + color[1][0], color[2], color[3]]
            else:
                clr = [COLOR_CMYK, [] + color[1][1], color[2], color[3]]
            return self.get_rgb_color(clr)
        res = self.do_transform(color, color[0], COLOR_RGB)
        return [COLOR_RGB, res, color[2], color[3]]

    def get_rgb_color255(self, color):
        return val_255(self.get_rgb_color(color)[1])

    def get_rgba_color255(self, color):
        clr = self.get_rgb_color(color)
        clr[1].append(clr[2])
        return val_255(clr[1])

    def get_cmyk_color(self, color):
        """
        Convert color into CMYK color.
        Stores alpha channel and color name.
        """
        if color[0] == COLOR_CMYK:
            return deepcopy(color)
        if color[0] == COLOR_SPOT:
            if color[1][1]:
                return [COLOR_CMYK, [] + color[1][1], color[2], color[3]]
            else:
                clr = [COLOR_RGB, [] + color[1][0], color[2], color[3]]
                return self.get_cmyk_color(clr)
        res = self.do_transform(color, color[0], COLOR_CMYK)
        return [COLOR_CMYK, res, color[2], color[3]]

    def get_cmyk_color255(self, color):
        return val_255(self.get_cmyk_color(color)[1])

    def get_lab_color(self, color):
        """
        Convert color into L*a*b* color.
        Stores alpha channel and color name.
        """
        if color[0] == COLOR_LAB:
            return deepcopy(color)
        if color[0] == COLOR_SPOT:
            if color[1][0]:
                color = [COLOR_RGB, [] + color[1][0], color[2], color[3]]
            else:
                color = [COLOR_CMYK, [] + color[1][1], color[2], color[3]]
        res = self.do_transform(color, color[0], COLOR_LAB)
        return [COLOR_LAB, res, color[2], color[3]]

    def get_grayscale_color(self, color):
        """
        Convert color into Grayscale color.
        Stores alpha channel and color name.
        """
        if color[0] == COLOR_GRAY:
            return deepcopy(color)
        if color[0] == COLOR_SPOT:
            if color[1][0]:
                color = [COLOR_RGB, [] + color[1][0], color[2], color[3]]
            else:
                color = [COLOR_CMYK, [] + color[1][1], color[2], color[3]]
        res = self.do_transform(color, color[0], COLOR_GRAY)
        return [COLOR_GRAY, res, color[2], color[3]]

    def get_color(self, color, cs=COLOR_RGB):
        """
        Convert color into requested colorspace.
        Stores alpha channel and color name.
        """
        methods_map = {COLOR_RGB: self.get_rgb_color,
                       COLOR_LAB: self.get_lab_color,
                       COLOR_CMYK: self.get_cmyk_color,
                       COLOR_GRAY: self.get_grayscale_color}
        return methods_map[cs](color)

    def mix_colors(self, color0, color1, coef=.5):
        supported = [COLOR_RGB, COLOR_CMYK, COLOR_GRAY]
        if not color0[0] in supported:
            return None
        if not color1[0] in supported:
            return None
        if not color0[0] == color1[0]:
            return None
        clr_vals = mix_lists(color0[1], color1[1], coef)
        alpha = mix_vals(color0[2], color1[2], coef)
        return [color0[0], clr_vals, alpha, '']

    def get_display_color(self, color):
        """
        Calcs display color representation.
        Returns list of RGB values.
        """
        if not self.use_cms:
            return self.get_rgb_color(color)[1]

        if color == COLOR_SPOT:
            if self.proof_for_spot:
                color = self.get_cmyk_color(color)
            else:
                color = self.get_rgb_color(color)

        cs_in = color[0]
        cs_out = COLOR_RGB
        if self.use_display_profile and COLOR_DISPLAY in self.handles:
            cs_out = COLOR_DISPLAY
        if self.proofing:
            if cs_in == COLOR_CMYK:
                ret = self.do_transform(color, cs_in, cs_out)
            elif cs_in == COLOR_SPOT:
                if self.proof_for_spot:
                    color = self.get_cmyk_color(color)
                else:
                    color = self.get_rgb_color(color)
                if color[0] == cs_out:
                    ret = color[1]
                else:
                    ret = self.do_transform(color, color[0], cs_out)
            else:
                ret = self.do_proof_transform(color, cs_in)
        else:
            if cs_in == cs_out:
                ret = color[1]
            elif cs_in == COLOR_SPOT:
                color = self.get_rgb_color(color)
                if color[0] == cs_out:
                    ret = color[1]
                else:
                    ret = self.do_transform(color, color[0], cs_out)
            else:
                ret = self.do_transform(color, cs_in, cs_out)
        return ret

    def get_display_color255(self, color):
        return val_255(self.get_display_color(color))

    def convert_image(self, img, outmode, cs_out=None):
        """
        Converts image between colorspaces.
        Returns new image instance.
        """
        if img.mode == IMAGE_MONO:
            img = img.convert(IMAGE_GRAY)
        if img.mode == outmode:
            return img.copy()
        if outmode == IMAGE_MONO:
            ret = self.do_bitmap_transform(img, IMAGE_GRAY, cs_out)
            return ret.convert(IMAGE_MONO)
        return self.do_bitmap_transform(img, outmode, cs_out)

    def adjust_image(self, img, profilestr):
        """
        Adjust image with embedded profile to similar colorspace
        defined by current profile.
        profilestr - embedded profile as a python string.
        Returns new image instance.
        """
        custom_profile = libcms.cms_open_profile_from_string(profilestr)
        cs_in = cs_out = IMAGE_TO_COLOR[img.mode]
        out_profile = self.handles[cs_in]
        intent = self.rgb_intent
        if cs_out == COLOR_CMYK:
            intent = self.cmyk_intent
        transform = libcms.cms_create_transform(custom_profile, cs_in,
                                                out_profile, cs_out, intent,
                                                self.flags)
        return libcms.cms_do_bitmap_transform(transform, img, cs_in, cs_out)

    def get_display_image(self, img):
        """
        Calcs display image representation.
        Returns new image instance.
        """

        outmode = IMAGE_RGB
        cs_out = None

        if not self.use_cms:
            return self.convert_image(img, outmode)

        if self.use_display_profile and COLOR_DISPLAY in self.handles:
            cs_out = COLOR_DISPLAY

        if self.proofing:
            if img.mode == IMAGE_CMYK:
                return self.convert_image(img, outmode, cs_out)
            else:
                return self.do_proof_bitmap_transform(img)
        else:
            return self.convert_image(img, outmode, cs_out)
