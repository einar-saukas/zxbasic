#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ts=4:et:sw=4:

# ----------------------------------------------------------------------
# Copyleft (K), Jose M. Rodriguez-Rosa (a.k.a. Boriel)
#
# This program is Free Software and is released under the terms of
#                    the GNU General License
# ----------------------------------------------------------------------

# ---- AST Symbols ----
from arglist import SymbolARGLIST as ARGLIST
from argument import SymbolARGUMENT as ARGUMENT
from arrayaccess import SymbolARRAYACCESS as ARRAYACCESS
from arraydecl import SymbolARRAYDECL as ARRAYDECL
from asm import SymbolASM as ASM
from binary import SymbolBINARY as BINARY
from block import SymbolBLOCK as BLOCK
from bound import SymbolBOUND as BOUND
from boundlist import SymbolBOUNDLIST as BOUNDLIST
from call import SymbolCALL as CALL
from const import SymbolCONST as CONST
from funcdecl import SymbolFUNCDECL as FUNCDECL
from id_ import SymbolID as ID
from number import SymbolNUMBER as NUMBER
from paramdecl import SymbolPARAMDECL as PARAMDECL
from paramlist import SymbolPARAMLIST as PARAMLIST
from sentence import SymbolSENTENCE as SENTENCE
from string_ import SymbolSTRING as STRING
from strslice import SymbolSTRSLICE as STRSLICE
from type_ import SymbolTYPE as TYPE
from typecast import SymbolTYPECAST as TYPECAST
from unary import SymbolUNARY as UNARY
from vardecl import SymbolVARDECL as VARDECL