# -*- coding: utf-8 -*-

from collections import defaultdict
from . import patterns

from .helpers import new_tmp_val, HI16, LO16
from .helpers import is_unknown, valnum, is_number
from .helpers import is_register, is_8bit_oper_register, is_16bit_composed_register


class Flags(object):
    def __init__(self):
        self.C = None
        self.Z = None
        self.P = None
        self.S = None


class CPUState(object):
    """ A class storing registers value information (CPU State).
    """
    def __init__(self):
        self.regs = None
        self.stack = None
        self.mem = None
        self._flags = None
        self._16bit = None
        self.reset()

    @property
    def Z(self):
        """ The Z flag
        """
        return self._flags[0].Z

    @Z.setter
    def Z(self, val):
        """ Sets the Z flag, and tries to update the F register accordingly.
        If the F register is unknown, sets it with a new unknown value.
        """
        assert val is None or val in 0, 1
        self._flags[0].Z = val
        if val is not None and is_number(self.regs['f']):
            self.regs['f'] = str((self.getv('f') & 0xBF) | (val << 6))
        else:
            self.regs['f'] = new_tmp_val()

    @property
    def C(self):
        """ The C flag
        """
        return self._flags[0].C

    @C.setter
    def C(self, val):
        """ Sets the C flag, and tries to update the F register accordingly.
        If the F register is unknown, sets it with a new unknown value.
        """
        assert val is None or val in 0, 1
        self._flags[0].C = val
        if val is not None and is_number(self.regs['f']):
            self.regs['f'] = str((self.getv('f') & 0xFE) | val)
        else:
            self.regs['f'] = new_tmp_val()

    @property
    def P(self):
        """ The P flag
        """
        return self._flags[0].P

    @P.setter
    def P(self, val):
        """ Sets the P flag, and tries to update the F register accordingly.
        If the F register is unknown, sets it with a new unknown value.
        """
        assert val is None or val in 0, 1
        self._flags[0].P = val
        if val is not None and is_number(self.regs['f']):
            self.regs['f'] = str((self.getv('f') & 0xFB) | (val << 2))
        else:
            self.regs['f'] = new_tmp_val()

    @property
    def S(self):
        """ The S flag
        """
        return self._flags[0].S

    @S.setter
    def S(self, val):
        """ Sets the S flag, and tries to update the F register accordingly.
        If the F register is unknown, sets it with a new unknown value.
        """
        assert val is None or val in 0, 1
        self._flags[0].S = val
        if val is not None and is_number(self.regs['f']):
            self.regs['f'] = str((self.getv('f') & 0x7F) | (val << 7))
        else:
            self.regs['f'] = new_tmp_val()

    def reset(self):
        """ Initial state
        """
        self.regs = {}
        self.stack = []
        self.mem = defaultdict(new_tmp_val)  # Dict of label -> value in memory
        self._flags = [Flags(), Flags()]

        for i in 'abcdefhl':
            self.regs[i] = new_tmp_val()  # Initial unknown state
            self.regs["%s'" % i] = new_tmp_val()

        self.regs['ixh'] = new_tmp_val()
        self.regs['ixl'] = new_tmp_val()
        self.regs['iyh'] = new_tmp_val()
        self.regs['iyl'] = new_tmp_val()
        self.regs['sp'] = new_tmp_val()
        self.regs['r'] = new_tmp_val()
        self.regs['i'] = new_tmp_val()

        for i in 'af', 'bc', 'de', 'hl':
            self.regs[i] = new_tmp_val()
            self.regs["%s'" % i] = new_tmp_val()

        self.regs['ix'] = new_tmp_val()
        self.regs['iy'] = new_tmp_val()

        self._16bit = {'b': 'bc', 'c': 'bc', 'd': 'de', 'e': 'de', 'h': 'hl', 'l': 'hl',
                       "b'": "bc'", "c'": "bc'", "d'": "de'", "e'": "de'", "h'": "hl'", "l'": "hl'",
                       'ixy': 'ix', 'ixl': 'ix', 'iyh': 'iy', 'iyl': 'iy', 'a': 'af', "a'": "af'",
                       'f': 'af', "f'": "af'"}

        self.reset_flags()

    def reset_flags(self):
        """ Resets flags to an "unknown state"
        """
        self.C = None
        self.Z = None
        self.P = None
        self.S = None

    def set(self, r, val):
        if val is None:
            is_num = False
            val = new_tmp_val()
        else:
            val = str(val)
            is_num = is_number(val)
            if is_num and self.getv(r) == valnum(val) & 0xFFFF:
                return  # The register already contains this value

        if r == '(sp)':
            if not self.stack:
                self.stack = [new_tmp_val()]

            self.stack[-1] = str(valnum(val) & 0xFFFF) if is_num else val
            return

        if r[0] == '(':  # (mem) <- r  => store in memory address
            r = r[1:-1].strip()
            if not patterns.RE_ID.match(r):
                return  # not an ID
            if r in self.mem and val == self.mem[r]:
                return  # the same value to the same pos does nothing... (strong assumption: NON-VOLATILE)
            if val not in self.regs:
                self.regs[val] = new_tmp_val()
            self.mem[r] = self.regs[val]
            return

        if val and val[0] == '(':  # r <- (mem)
            v_ = val[1:-1].strip()
            if patterns.RE_ID.match(v_):
                if v_ in self.mem:
                    val = self.mem[v_]
                else:
                    val = self.mem[v_] = new_tmp_val()
            else:
                val = new_tmp_val()

        if is_8bit_oper_register(r):
            if is_register(val):
                val = self.regs[r] = self.regs[val]
            else:
                if is_num:
                    oldval = self.getv(r)
                    val = str(valnum(val) & 0xFF)
                    if val == oldval:  # Does not change
                        return
                self.regs[r] = val

            if r not in self._16bit:
                return

            hl = self._16bit[r]
            self.mem[hl] = new_tmp_val()  # Changing a 16 bit regs means changing the content of its *memptr

            if not is_num or not is_number(self.regs[hl]):
                self.regs[hl] = new_tmp_val()  # unknown
                return

            val = int(val)
            if r in {'b', 'd', 'h', 'ixh', 'iyh', "b'", "d'", "h'"}:  # high register
                self.regs[hl] = str((val << 8) + int(self.regs[LO16(hl)]))
            else:
                self.regs[hl] = str((self.regs[HI16(hl)] << 8) + val)

            return

        # a 16 bit reg
        self.regs[r] = val
        if is_16bit_composed_register(r):  # sp register is not included. Special case
            self.mem[r] = new_tmp_val()

            if not is_num:
                self.regs[LO16(r)] = new_tmp_val()
                self.regs[HI16(r)] = new_tmp_val()
            else:
                val = valnum(val)
                self.regs[LO16(r)] = str(val & 0xFF)
                self.regs[HI16(r)] = str(val >> 8)

            if 'f' in r:
                self.reset_flags()

    def get(self, r):
        """ Returns precomputed value of the given expression
        """
        if r is None:
            return None

        if r.lower() == '(sp)' and self.stack:
            return self.stack[-1]

        if r[:1] == '(':
            return self.mem[r[1:-1]]

        r = r.lower()
        if is_number(r):
            return str(valnum(r))

        if not is_register(r):
            return None

        return self.regs[r]

    def getv(self, r):
        """ Like the above, but returns the <int> value.
        """
        v = self.get(r)
        if not is_unknown(v):
            try:
                v = int(v)
            except ValueError:
                v = None
        else:
            v = None
        return v

    def eq(self, r1, r2):
        """ True if values of r1 and r2 registers are equal
        """
        if not is_register(r1) or not is_register(r2):
            return False

        if self.regs[r1] is None or self.regs[r2] is None:  # HINT: This's been never USED??
            return False

        return self.regs[r1] == self.regs[r2]

    def set_flag(self, val):
        if not is_number(val):
            self.regs['f'] = new_tmp_val()
            self.reset_flags()
            return

        self.set('f', val)
        val = valnum(val)
        self.C = val & 1
        self.P = (val >> 2) & 1
        self.Z = (val >> 6) & 1
        self.S = (val >> 7) & 1

    def inc(self, r):
        """ Does inc on the register and precomputes flags
        """
        self.set_flag(None)

        if not is_register(r):
            if r[0] == '(':  # a memory position, basically: inc(hl)
                r_ = r[1:-1].strip()
                v_ = self.getv(self.mem.get(r_, None))
                if v_ is not None:
                    v_ = (v_ + 1) & 0xFF
                    self.mem[r_] = str(v_)
                    self.Z = int(v_ == 0)  # HINT: This might be improved
                else:
                    self.mem[r_] = new_tmp_val()
            return

        if self.getv(r) is not None:
            self.set(r, self.getv(r) + 1)
        else:
            self.set(r, None)

    def dec(self, r):
        """ Does dec on the register and precomputes flags
        """
        self.set_flag(None)

        if not is_register(r):
            if r[0] == '(':  # a memory position, basically: inc(hl)
                r_ = r[1:-1].strip()
                v_ = self.getv(self.mem.get(r_, None))
                if v_ is not None:
                    v_ = (v_ - 1) & 0xFF
                    self.mem[r_] = str(v_)
                    self.Z = int(v_ == 0)  # HINT: This might be improved
                else:
                    self.mem[r_] = new_tmp_val()
            return

        if self.getv(r) is not None:
            self.set(r, self.getv(r) - 1)
        else:
            self.set(r, None)

    def rrc(self, r):
        """ Does a ROTATION to the RIGHT |>>
        """
        if not is_number(self.regs[r]):
            self.set(r, None)
            self.set_flag(None)
            return

        v_ = self.getv(self.regs[r]) & 0xFF
        self.regs[r] = str((v_ >> 1) | ((v_ & 1) << 7))

    def rr(self, r):
        """ Like the above, bus uses carry
        """
        if self.C is None or not is_number(self.regs[r]):
            self.set(r, None)
            self.set_flag(None)
            return

        self.rrc(r)
        tmp = self.C
        v_ = self.getv(self.regs[r])
        self.C = v_ >> 7
        self.regs[r] = str((v_ & 0x7F) | (tmp << 7))

    def rlc(self, r):
        """ Does a ROTATION to the LEFT <<|
        """
        if not is_number(self.regs[r]):
            self.set(r, None)
            self.set_flag(None)
            return

        v_ = self.getv(self.regs[r]) & 0xFF
        self.set(r, ((v_ << 1) & 0xFF) | (v_ >> 7))

    def rl(self, r):
        """ Like the above, bus uses carry
        """
        if self.C is None or not is_number(self.regs[r]):
            self.set(r, None)
            self.set_flag(None)
            return

        self.rlc(r)
        tmp = self.C
        v_ = self.getv(self.regs[r])
        self.C = v_ & 1
        self.regs[r] = str((v_ & 0xFE) | tmp)

    def _is(self, r, val):
        """ True if value of r is val.
        """
        if not is_register(r) or val is None:
            return False

        r = r.lower()
        if is_register(val):
            return self.eq(r, val)

        if is_number(val):
            val = str(valnum(val))
        else:
            val = str(val)

        if val[0] == '(':
            val = self.mem[val[1:-1]]

        return self.regs[r] == val

    def op(self, i, o):
        """ Tries to update the registers values with the given
        instruction.
        """
        for ii in range(len(o)):
            if is_register(o[ii]):
                o[ii] = o[ii].lower()

        if i == 'ld':
            self.set(o[0], o[1])
            return

        if i == 'push':
            if valnum(self.regs['sp']):
                self.set('sp', (self.getv(self.regs['sp']) - 2) % 0xFFFF)
            else:
                self.set('sp', None)
            self.stack.append(self.regs[o[0]])
            return

        if i == 'pop':
            self.set(o[0], self.stack and self.stack.pop() or None)
            if valnum(self.regs['sp']):
                self.set('sp', (self.getv(self.regs['sp']) + 2) % 0xFFFF)
            else:
                self.set('sp', None)
            return

        if i == 'inc':
            self.inc(o[0])
            return

        if i == 'dec':
            self.dec(o[0])
            return

        if i == 'rra':
            self.rr('a')
            return
        if i == 'rla':
            self.rl('a')
            return
        if i == 'rlca':
            self.rlc('a')
            return
        if i == 'rrca':
            self.rrc('a')
            return
        if i == 'rr':
            self.rr(o[0])
            return
        if i == 'rl':
            self.rl(o[0])
            return

        if i == 'exx':
            for j in 'bc', 'de', 'hl' 'b', 'c', 'd', 'e', 'h', 'l':
                self.regs[j], self.regs["%s'" % j] = self.regs["%s'" % j], self.regs[j]
            return

        if i == 'ex':
            for j in 'af', 'a', 'f':
                self.regs[j], self.regs["%s'" % j] = self.regs["%s'" % j], self.regs[j]
            return

        if i == 'xor':
            self.setC(0)

            if o[0] == 'a':
                self.set('a', 0)
                self.setZ(1)
                return

            if self.getv('a') is None or self.getv(o[0]) is None:
                self.setZ(None)
                self.set('a', None)
                return

            self.set('a', self.getv('a') ^ self.getv(o[0]))
            self.setZ(int(self.get('a') == 0))
            return

        if i in ('or', 'and'):
            self.setC(0)

            if self.getv('a') is None or self.getv(o[0]) is None:
                self.setZ(None)
                self.set('a', None)
                return

            if i == 'or':
                self.set('a', self.getv('a') | self.getv(o[0]))
            else:
                self.set('a', self.getv('a') & self.getv(o[0]))

            self.setZ(int(self.get('a') == 0))
            return

        if i in ('adc', 'sbc'):
            if len(o) == 1:
                o = ['a', o[0]]

            if self.C is None:
                self.set(o[0], 'None')
                self.setZ(None)
                self.set(o[0], None)
                return

            if i == 'sbc' and o[0] == o[1]:
                self.setZ(int(not self.C))
                self.set(o[0], -self.C)
                return

            if self.getv(o[0]) is None or self.getv(o[1]) is None:
                self.set_flag(None)
                self.set(o[0], None)
                return

            if i == 'adc':
                val = self.getv(o[0]) + self.getv(o[1]) + self.C
                if is_8bit_oper_register(o[0]):
                    self.setC(int(val > 0xFF))
                else:
                    self.setC(int(val > 0xFFFF))
                self.set(o[0], val)
                return

            val = self.getv(o[0]) - self.getv(o[1]) - self.C
            self.C = int(val < 0)
            self.Z = int(val == 0)
            self.set(o[0], val)
            return

        if i in ('add', 'sub'):
            if len(o) == 1:
                o = ['a', o[0]]

            if i == 'sub' and o[0] == o[1]:
                self.Z = 1
                self.C = 0
                self.set(o[0], 0)
                return

            if not is_number(self.get(o[0])) or not is_number(self.get(o[1])) is None:
                self.set_flag(None)
                self.set(o[0], None)
                return

            if i == 'add':
                val = self.getv(o[0]) + self.getv(o[1])
                if is_8bit_oper_register(o[0]):
                    self.C = int(val > 0xFF)
                    val &= 0xFF
                    self.Z = int(val == 0)
                    self.S = val >> 7
                else:
                    self.C = int(val > 0xFFFF)
                    val &= 0xFFFF

                self.set(o[0], val)
                return

            val = self.getv(o[0]) - self.getv(o[1])
            if is_8bit_oper_register(o[0]):
                self.C = int(val < 0)
                val &= 0xFF
                self.Z = int(val == 0)
                self.S = val >> 7
            else:
                self.C = int(val < 0)
                val &= 0xFFFF

            self.set(o[0], val)
            return

        if i == 'neg':
            if self.getv('a') is None:
                self.set_flag(None)
                return

            val = -self.getv('a')
            self.set('a', val)
            self.Z = int(not val)
            val &= 0xFF
            self.S = val >> 7
            return

        if i == 'scf':
            self.C = 1
            return

        if i == 'ccf':
            if self.C is not None:
                self.C = int(not self.C)
            return

        if i == 'cpl':
            if self.getv('a') is None:
                return

            self.set('a', 0xFF ^ self.getv('a'))
            return

        # Unknown. Resets ALL
        self.reset()