# -*- coding: utf-8 -*-
"""
UV-vis text parser.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import re

from .base import BaseSentenceParser
#from ..relex import ChemicalRelationship
from ..parse import R, I, W, Optional, merge, join, OneOrMore, Any, ZeroOrMore, Start
from ..parse.cem import chemical_name, chemical_label,ion_symbol,transition_metals,ion_label,name_with_doped_label,element_symbol,lanthanides
from ..parse.base import BaseParser
from ..parse.common import lrb, rrb, delim, colon, optdelim, hyphen
from ..utils import first
from .actions import strip_stop
#from ..doc import Document
#from ..doc import Paragraph, Heading, Sentence
from lxml import etree
import pprint
import unittest
import logging
import io
import os


log = logging.getLogger(__name__)

Specifier = (I('emission')+R('.*?')+I('nm$')|I('emi(t|tted|tting|ts)')|I('em$')|I('emission')+I('peak')|
                                             R('λ')+I('em')|I('emission')+I('ma(x|xmium)')|I('peak(s|ing).*?at')|R('\u03bb')+I('em')|
                                             I('emission')+I('at'))('specifier').add_action(join)
delim = R('^[,:;\./]$') | W(' ') 
Specifier.tag = 'specifier'
units = (W('nm'))('units').add_action(merge)
units.tag = 'units'
value = (R('^\d{3}(\.\,\d+)?$'))('value').add_action(join)
value.tag = 'value'
multipeaks = (value + ZeroOrMore((I('and')|delim | hyphen| I('to')) + value) )
peaks = (value + ZeroOrMore((delim | hyphen| I('to')) + value))('peaks').add_action(join)
peaks.tag = 'peaks'
#formula = (
 ##   R('^(\(?\[?\(?(A([glmru]|(s\d\.?))|B[ahikr]?|C[adeflmnorsu(\d)]?|D[bsy]|E[rsu]?|F[elmr$]?|G[ade]|H[efgos]|I[rn]?|K[r(\d\.?)]?|(L[airuv])|M[dgnot]?|N[abdeip(\d\.?)]?|O[s\d.]?|P[abdmotuOr\d]?|R[abefghnuE]?|S[bcegimnr(\d\.?)]?|T[abehil\d]|U(u[opst])|V|Xe|Yb?|Z[nr])(\)?\]?\)?([\d.]+)?(x?\-?[\d.]+\-?x?)?)){2,}(\+[δβγ])?'))
#Doped_ion = (
#             R(':') +(ion_symbol|transition_metals+ion_label))
##concentration = (R('x')|R('y'))
#concentration_range = R('\(.+\)$')
formula = (
    R('^(\(?\[?\(?(A([glmru]|(s\d\.?))|B[ahikr]?|C[adeflmnorsu(\d)]?|D[bsy]|E[rsu]?|F[elmr$]?|G[ade]|H[efgos]|I[rn]?|K[r(\d\.?)]?|(L[airuvn])|M[dgnot]?|N[abdeip(\d\.?)]?|O[s\d.]?|P[abdmotuOr\d]?|R[abefghnuE]?|S[bcegimnr(\d\.?)]?|T[abehil\d]|U(u[opst])|V|Xe|x|Yb?|Z[nr])(\)?\]?\)?([\d.]+)?(x?y?\-?\+?\/?[\d.]+\-?\+?\/?x?y?)?(\/)?)){2,}(\+?[δβγ])?'))
Doped_ion = (
             R(':') +(ion_symbol|transition_metals+ion_label) 
)
co_doped = (Doped_ion + delim + (ion_symbol|transition_metals+ion_label))
concentration = (R(':') +(R('x')|R('y'))+(ion_symbol|transition_metals+ion_label)) 
concentration_range = R('\(.*\)$')
add_content = (R('^\((x|y|δ|β|0-9|A-Z).?=?.?\)$'))
phosphor = (((formula + Doped_ion)|
            (formula + Doped_ion + add_content)|
            (formula+co_doped)|chemical_name|name_with_doped_label|
            (formula + concentration + concentration_range ))+ZeroOrMore(add_content))('phosphor').add_action(join)

#phosphor = ((formula + Doped_ion)|chemical_name|name_with_doped_label|(formula + concentration + Doped_ion + concentration_range ))('phosphor').add_action(join)
#doped_ion = (ion_symbol|transition_metals+ion_label|lanthanides|element_symbol+ion_label|chemical_name)('doped_ion').add_action(join)
#doped_ion = (chemical_name)('doped_ion').add_action(join)
phosphor.tag = 'phosphor'
entities = (phosphor|Specifier|peaks+units)
pc_phrase = (entities + OneOrMore(entities | Any()))('emission_peak')
pc_entities = [phosphor,Specifier,peaks,units]
#pc_relationship = ChemicalRelationship(pc_entities,pc_phrase,name='emission_peak')



class epParser(BaseSentenceParser):
    """"""
    root = pc_phrase

    def interpret(self, result, start, end):
        #u = self.model(phosphor = result.get('phosphor'),specifier = result.get('specifier'),peaks = result.get('peaks'),units = result.get('units'))
        a = self.model(phosphor = first(result.xpath('//phosphor/text()')),
                       specifier = first(result.xpath('//Specifier/text()')),
                       peaks = first(result.xpath('//peaks/text()')),
                       units = first(result.xpath('//units/text()'))
        )

        yield a
