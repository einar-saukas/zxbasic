#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ts=4:et:sw=4:

# ----------------------------------------------------------------------
# Copyleft (K), Jose M. Rodriguez-Rosa (a.k.a. Boriel)
#
# This program is Free Software and is released under the terms of
#                    the GNU General License
# ----------------------------------------------------------------------
from typing import Optional

from src.api.constants import CLASS
from src.api.constants import KIND
import src.api.errmsg
from .var import SymbolVAR
from .paramlist import SymbolPARAMLIST
from .block import SymbolBLOCK


class SymbolFUNCTION(SymbolVAR):
    """ This class expands VAR top denote Function declarations
    """

    def __init__(self, varname, lineno, offset=None, type_=None):
        super(SymbolFUNCTION, self).__init__(varname, lineno, offset, class_=CLASS.function, type_=type_)
        self.reset()

    def reset(self, lineno=None, offset=None, type_=None):
        """ This is called when we need to reinitialize the instance state
        """
        self.lineno = self.lineno if lineno is None else lineno
        self.type_ = self.type_ if type_ is None else type_
        self.offset = self.offset if offset is None else offset

        self.callable = True
        self.params = SymbolPARAMLIST()
        self.body = SymbolBLOCK()
        self.__kind = KIND.unknown
        self.local_symbol_table = None

    @property
    def kind(self):
        return self.__kind

    def set_kind(self, value, lineno):
        assert KIND.is_valid(value)

        if self.__kind != KIND.unknown and self.__kind != value:
            q = KIND.to_string(KIND.sub) if self.__kind == KIND.function else KIND.to_string(KIND.function)
            src.api.errmsg.error(lineno, "'%s' is a %s, not a %s" %
                                 (self.name, KIND.to_string(self.__kind).upper(), q.upper()))
        self.__kind = value

    @property
    def params(self) -> SymbolPARAMLIST:
        if not self.children:
            return SymbolPARAMLIST()
        return self.children[0]

    @params.setter
    def params(self, value: SymbolPARAMLIST):
        assert isinstance(value, SymbolPARAMLIST)
        if self.children is None:
            self.children = []

        if self.children:
            self.children[0] = value
        else:
            self.children = [value]

    @property
    def body(self) -> SymbolBLOCK:
        if not self.children or len(self.children) < 2:
            self.body = SymbolBLOCK()

        return self.children[1]

    @body.setter
    def body(self, value: Optional[SymbolBLOCK]):
        if value is None:
            value = SymbolBLOCK()
        assert isinstance(value, SymbolBLOCK)

        if self.children is None:
            self.children = []

        if not self.children:
            self.params = SymbolPARAMLIST()

        if len(self.children) < 2:
            self.children.append(value)
        else:
            self.children[1] = value

    def __repr__(self):
        return 'FUNC:{}'.format(self.name)
