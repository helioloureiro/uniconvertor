# -*- coding: utf-8 -*-
#
#  Copyleft  (L) 2021 by Helio Loureiro
#  Copyright (C) 2017-2018 by Ihor E. Novikov
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

import logging

from uc2.utils import fsutils

LOG = logging.getLogger(__name__)


class SerializedConfig(object):
    """
    Represents parent class for application configs.
    """
    filename = ''

    def update(self, cnf=None):
        cnf = cnf or {}
        if cnf:
            for key in cnf.keys():
                if hasattr(self, key):
                    setattr(self, key, cnf[key])

    def load(self, filename=None):
        self.filename = filename
        if fsutils.exists(filename):
            try:
                fileobj = fsutils.get_fileptr(filename)
            except Exception:
                return

            while True:
                line = fileobj.readline()
                if line.startswith('<?xml') or not line:
                    break
                if line.startswith('#'):
                    continue
                line = fsutils.get_utf8_path('self.%s' % line)
                try:
                    code = compile(line, '<string>', 'exec')
                    exec(code)
                except Exception as e:
                    LOG.error('ERROR>>> %s\n%s', line, e)
            fileobj.close()

    def save(self, filename=None):
        if self.filename and filename is None:
            filename = self.filename
        if len(self.__dict__) == 0 or filename is None:
            return

        try:
            fileobj = fsutils.get_fileptr(filename, True)
        except Exception:
            return

        defaults = SerializedConfig.__dict__
        items = self.__dict__.items()
        items.sort()
        for key, value in items:
            if key in defaults and defaults[key] == value:
                continue
            if key in ['filename', 'app']:
                continue
            try:
                line = fsutils.get_sys_path('%s = %s\n' % (key, value.__repr__()))
            except Exception as e:
                LOG.error('ERROR>>> %s', e)
                continue
            fileobj.write(line)
        fileobj.close()
