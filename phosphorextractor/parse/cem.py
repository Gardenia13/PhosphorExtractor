# -*- coding: utf-8 -*-
"""
Chemical entity mention parser elements.
..codeauthor:: Matt Swain (mcs07@cam.ac.uk)
..codeauthor:: Callum Court (cc889@cam.ac.uk)

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from abc import abstractproperty, abstractmethod
import logging
import re
from lxml import etree
from . import merge
from .actions import join, fix_whitespace
from .common import roman_numeral,colon, cc, nnp, hyph, nns, nn, cd, ls, optdelim, bcm, icm, rbrct, lbrct, sym, jj, hyphen, quote, \
    dt, delim,slash
from .base import BaseSentenceParser, BaseTableParser
from .elements import I, R, W, T, ZeroOrMore, Optional, Not, Group, End, Start, OneOrMore, Any, SkipTo
from lxml import etree


log = logging.getLogger(__name__)

joining_characters = R('^\@|\/$')

alphanumeric = R('^(d-)?(\d{1,2}[A-Za-z]{1,2}[′″‴‶‷⁗]?)(-d)?$')

numeric = R('^\d{1,3}$')

letter_number = R('^(H\d)?[LSNM]{1,2}\d\d?$')

# Blacklist to truncate chemical mentions where tags continue on incorrectly
cm_blacklist = (W('in') | I('electrodes') | I('anodes') | I('specimen') | I('and') | R('^m\.?p\.?$', re.I) |R('^N\.?M\.?R\.?\(?$', re.I))

exclude_prefix = Start() + (lbrct + roman_numeral + rbrct + Not(hyphen) | (R('^\d{1,3}(\.\d{1,3}(\.\d{1,3}(\.\d{1,3})?)?)?$') + Not(hyphen)) | (I('stage') | I('step') | I('section') | I('part')) + (alphanumeric | numeric | roman_numeral | R('^[A-Z]$')))

# Tagged chemical mentions - One B-CM tag followed by zero or more I-CM tags.
cm = (exclude_prefix.hide() + OneOrMore(Not(cm_blacklist) + icm)) | (bcm + ZeroOrMore(Not(cm_blacklist) + icm)).add_action(join)

comma = (W(',') | T(',')).hide()
#colon = (W(':') | T(':')).hide()

# Prefixes to include in the name
include_prefix = Not(bcm) + R('^(deuterated|triflated|butylated|brominated|acetylated|twisted)$', re.I)

label_type = (Optional(I('reference') | I('comparative')) + R('^(compound|ligand|chemical|dye|derivative|complex|example|intermediate|product|formulae?|preparation|specimen)s?$', re.I))('roles').add_action(join) + Optional(colon).hide()

synthesis_of = ((I('synthesis') | I('preparation') | I('production') | I('data')) + (I('of') | I('for')))('roles').add_action(join)

to_give = (I('to') + (I('give') | I('yield') | I('afford')) | I('afforded') | I('affording') | I('yielded'))('roles').add_action(join)

label_blacklist = R('^(wR.*|R\d|31P|[12]H|[23]D|15N|14C|[4567890]\d+|2A)$')

prefixed_label = R('^(cis|trans)-((d-)?(\d{1,2}[A-Za-z]{0,2}[′″‴‶‷⁗]?)(-d)?|[LS]\d\d?)$')

#: Chemical label. Very permissive - must be used in context to avoid false positives.
strict_chemical_label = Not(label_blacklist) + (alphanumeric | roman_numeral | letter_number | prefixed_label)('labels')

lenient_chemical_label = numeric('labels') | R('^([A-Z]\d{1,3})$')('labels') | strict_chemical_label

chemical_label = ((label_type + lenient_chemical_label + ZeroOrMore((T('CC') | comma) + lenient_chemical_label)) | (Optional(label_type.hide()) + strict_chemical_label + ZeroOrMore((T('CC') | comma) + strict_chemical_label)))

#: Chemical label with a label type before
chemical_label_phrase1 = (Optional(synthesis_of) + label_type + lenient_chemical_label + ZeroOrMore((T('CC') | comma) + lenient_chemical_label))
#: Chemical label with synthesis of before
chemical_label_phrase2 = (synthesis_of + Optional(label_type) + lenient_chemical_label + ZeroOrMore((T('CC') | comma) + lenient_chemical_label))
# Chemical label with to give/afforded etc. before, and some restriction after.
chemical_label_phrase3 = (to_give + Optional(dt) + Optional(label_type) + lenient_chemical_label + Optional(lbrct + OneOrMore(Not(rbrct) + Any()) + rbrct).hide() + (End() | I('as') | colon | comma).hide())

###### DOPED CHEMICAL LABELS ##########
doped_chemical_identifier = (W('x') | W('y') | colon)
doping_value = R('^(\d\.?)+$')
doping_range = (doping_value + (T('HYPH')|I('to')) + doping_value)

doping_label_1 = (doping_value + R('^\<$') + doped_chemical_identifier +
                  R('^\<$') + doping_value)
doping_label_2 = (
    doped_chemical_identifier
    + W('=')
    + OneOrMore(doping_range | doping_value | R('^[,:;\.]$') | I('or') | I('and')))

doped_chemical_label = Group((doping_label_1 | doping_label_2)('labels')).add_action(join)
chemical_label_phrase = Group(doped_chemical_label | chemical_label_phrase1 | chemical_label_phrase2 | chemical_label_phrase3)('chemical_label_phrase')

###### INFORMAL CHEMICAL LABELS ##########
# Identifiers typically used as informal chemical symbols
informal_chemical_symbol = (W('AE') | W('T') | W('RE') | (W('R') + Not(lbrct + W('Å') + rbrct)) | W('REM') | W('REO') | W('REY') | W('LREE') | W('HREE') | I('Ln') | R('^B\′?$') | W('M') | W('ET')
                                | W('IM2py') | W('NN′3') | W('TDAE') | W('X') | I('H2mal') | (W('A') + Not(lbrct + W('Å') + rbrct)))
# list of chemical elements or ion symbols by type
metals = (
            R('^(Li|Be|Na|Mg|Al|Ca|Sc|Ti|V|Cr|K|Mn|Fe|Co|Ni|Cu|Zn|Ga|Rb|Sr|Y|Zr|Nb|Mo|Tc|Ru|Rh|Pd|Ag|Cd|In|Sn|Cs|Ba|La|Ce|Pr|Nd|Pm|Sm|Eu|Gd|Tb|Dy|Ho|Er|Tm|Yb|Lu|Hf|Ta|W|Re|Os|Ir|Pt|Au|Hg|Tl|Pb|Bi|Po|Fr|Ra|Ac|Th|Pa|U|Np|Pu|Am|Cm|Bk|Cf|Es|Fm|Md|No|Lr|Rf|Db|Sg|Bh|Hs|Mt|Ds|Rg|Cn|Uut|Fl|Uup|Lv)$') | R(
        '^metal(s)?$'))
transition_element = (R('^(Sc|Ti|V|Cr|Mn|Fe|Co|Ni|Cu|Zn|Y|Zr|Nb|Mo|Tc|Ru|Rh|Pd|Ag|Cd|La|Ce|Pr|Nd|Pm|Sm|Eu|Gd|Tb|Dy|Ho|Er|Tm|Yb|Lu|Hf|Ta|W|Re|Os|Ir|Pt|Au|Hg|Ac|Th|Pa|U|Np|Pu|Am|Cm|Bk|Cf|Em|Fm|Md|No|Lr|Rf|Db|Sg|Bh|Hs|Mt|Ds|Rg|Cn)$'))
transition_metals = (
            R('^(Sc|Ti|V|Cr|Mn|Fe|Co|Ni|Cu|Zn|Y|Zr|Nb|Mo|Tc|Ru|Rh|Pd|Ag|Cd|La|Ce|Pr|Nd|Pm|Sm|Eu|Gd|Tb|Dy|Ho|Er|Tm|Yb|Lu|Hf|Ta|W|Re|Os|Ir|Pt|Au|Hg|Ac|Th|Pa|U|Np|Pu|Am|Cm|Bk|Cf|Em|Fm|Md|No|Lr|Rf|Db|Sg|Bh|Hs|Mt|Ds|Rg|Cn)') | (
            I('transition') + (I('metal') | I('metals'))))
lanthanides = (R('^(Sc|Y|La|Ce|Pr|Nd|Pm|Sm|Eu|Gd|Tb|Dy|Ho|Er|Tm|Yb|Lu)$') | R('^[Ll]anthanide(s)?$') | (
        R('^[Rr]are\-?earth(s)?$') | (
            I('rare') + Optional(T('HYPH')) + R(('^earth(s)?$')) + Optional(R('^metal(s)?$')))))
ion_symbol = (
    R('^(Ti|V|Cr|Mn|Fe|Co|Ni|Cu|Ce|Ir|Pr|Nd|Pm|Sm|Eu|Bi|Gd|Tb|Dy|Ho|Er|Tm|Yb|Li|Be|Na|Al|As)(((2|3|4|5|6|7)?\+?)|(I{2,7}))?$'
      ))
ion_label = (R('(((2|3|4|5|6|7)?\+?)|(I{2,7}))?$'))


other_symbol = (W('NO3') | W('HF2') | W('ClO4') | W('BF4'))

informal_values = (metals | transition_metals | lanthanides | ion_symbol | other_symbol)

# Informal labelling, used for associating properties to informal compounds
informal_chemical_label_1 = (informal_chemical_symbol
                             + W('=')
                             + OneOrMore(informal_values | R('^[,:;\.]$') | I('and') | informal_chemical_symbol | W('=')))('label').add_action(join)

# Informal label phrase 2, "property = value for the <element> compound"
informal_chemical_label_2 = (informal_values
                            + (I('compound') | I('sample') | I('material')).hide())('label').add_action(join)

informal_chemical_label = Group((informal_chemical_label_1 | informal_chemical_label_2)('labels')).add_action(join)
chemical_label_phrase = Group(informal_chemical_label | doped_chemical_label | chemical_label_phrase1 | chemical_label_phrase2 | chemical_label_phrase3)('chemical_label_phrase')

# TODO: "Compound 3a-c" - in parser expand out into multiple compounds

element_name = R('^(actinium|aluminium|aluminum|americium|antimony|argon|arsenic|astatine|barium|berkelium|beryllium|bismuth|bohrium|boron|bromine|cadmium|caesium|calcium|californium|carbon|cerium|cesium|chlorine|chromium|cobalt|copernicium|copper|curium|darmstadtium|dubnium|dysprosium|einsteinium|erbium|europium|fermium|flerovium|fluorine|francium|gadolinium|gallium|germanium|hafnium|hassium|helium|holmium|hydrargyrum|hydrogen|indium|iodine|iridium|iron|kalium|krypton|lanthanum|laIrencium|lithium|livermorium|lutetium|magnesium|manganese|meitnerium|mendelevium|mercury|molybdenum|natrium|neodymium|neon|neptunium|nickel|niobium|nitrogen|nobelium|osmium|oxygen|palladium|phosphorus|platinum|plumbum|plutonium|polonium|potassium|praseodymium|promethium|protactinium|radium|radon|rhenium|rhodium|roentgenium|rubidium|ruthenium|rutherfordium|samarium|scandium|seaborgium|selenium|silicon|silver|sodium|stannum|stibium|strontium|sulfur|tantalum|technetium|tellurium|terbium|thallium|thorium|thulium|tin|titanium|tungsten|ununoctium|ununpentium|ununseptium|ununtrium|uranium|vanadium|Iolfram|xenon|ytterbium|yttrium|zinc|zirconium)$', re.I)

#: Mostly unambiguous element symbols
element_symbol = R('^(Ag|Au|Br|Cd|Cl|Cu|Fe|Gd|Ge|Hg|Mg|Pb|Pd|Pt|Ru|Sb|Si|Sn|Ti|Xe|Zn|Zr)$')

#: Registry number patterns
registry_number = R('^BRN-?\d+$') | R('^CHEMBL-?\d+$') | R('^GSK-?\d{3-7}$') | R('^\[?(([1-9]\d{2,7})|([5-9]\d))-\d\d-\d\]?$')

#: Amino acid abbreviations. His removed, too ambiguous
amino_acid = R('^((Ala|Arg|Asn|Asp|Cys|Glu|Gln|Gly|Ile|Leu|Lys|Met|Phe|Pro|Ser|Thr|Trp|Tyr|Val)-?)+$')

amino_acid_name = (
    R('^(histidine|isoleucine|leucine|lysine|methionine|phenylalanine|threonine|tryptophan|valine|selenocysteine|serine|tyrosine|alanine|arginine|asparagine|cysteine|glutamine|glycine|proline)$', re.I) |
    I('aspartic') + I('acid') | I('glutamic') + I('acid')
)

#: Chemical formula patterns, updated to include Inorganic compound formulae
formula = (
    R('^(\(?\[?\(?(A([glmru]|(s\d\.?))|B[ahikr]?|C[adeflmnorsu(\d)]|D[bsy]|E[rsu]|F[elmr$]|G[ade]|H[efgos]|I[rn][1-9]?|K[r(\d\.?)]|(L[airuv])|M[dgnot]|N[abdeip(\d\.?)]|O[s\d.]?|P[abdmotuOr\d]|R[abefghnuE]|S[bcegimnr(\d\.?)]|T[abehil\d]|U(u[opst])|V|Xe|Yb?|Z[nr])(\)?\]?\)?([\d.]+)?)+){2,}(\+[δβαγ])?') |
    R('^((\(?\d{2,3}\)?)?(Fe|Ti|Mg|Ru|Cd|Se)\(?(\d\d?|[IV]+)?\)?((O|Hg)\(?\d?\d?\)?)?)+(\(?\d?[\+\-]\d?\)?)?$') |
    R('(NO\d|BH4|Ca\(2\+\)|Ti\(0\)2|\(CH3\)2CHOH|\(CH3\)2CO|\(CH3\)2NCOH|C2H5CN|CH2ClCH2Cl|CH3C6H5|CH3CN|CH3CO2H|CH3COCH3|CH3COOH|CH3NHCOH|CH3Ph|CH3SOCH3|Cl2CH2|ClCH2CH2Cl)') |
    R('^[\[\{\(]{1,2}(Ru|Ph|Py|Cu|Ir|Pt|Et\d).*[\]\}\)]$')
)

doped_ion = (colon
             +ZeroOrMore(R('\d+(\.\d+)?'))
             +ZeroOrMore(R('(wt)?%'))
             +ZeroOrMore(I('x'))
             +ZeroOrMore(I('y'))
             +OneOrMore((ion_symbol|transition_metals+ion_label)+ZeroOrMore(R('\\\\')))
             )

cation_1 = R('^(Ca|Ba|Sr|Na|K|Rb|Y|Zn|La|Mg|Al|Li|Gd|Cs|Co|Ga|As|In|Sn|Pb|Bi|I|Br|At|Sb|Te|Se|Po|W|Au|Hg|Pd|Ag|Cu|Ni|Cd|Pt|Pb|Be|B|Al|Si|Ge|Sn|Pb)?$')
cation_1g = cation_1 + Optional(R('\d+(\.\d+)?$'))
anion_1 = R('^(O|N|Cl|S|F|Br|I)?$')
anion_1g = cation_1g + Optional(R('\d+(\.\d+)?$'))
dopant_expr = delim +Optional(R('\s'))+Optional(I('x'))+Optional(I('y'))+ doped_ion
phosphor_number = R('(\d+(\.\d+)?)')
phosphor_formula_1 = OneOrMore(cation_1g) + OneOrMore(anion_1g)
phosphor_formula_dop = phosphor_formula_1 +Optional(R('\s'))+ dopant_expr
phosphor_formula = (metals+phosphor_number)+ R('.?') + Optional(R('\s'))+Optional(I('x'))+Optional(I('y'))+Optional(phosphor_number) + ion_symbol
phosphor_formula2 = (formula + delim + ion_symbol)
Doped_ion = (
             R('[:：]') +(ion_symbol|transition_metals+ion_label)
)
phosphors = (
    I('Ca19Mn2(PO4)14')|I('(Sr0.5Eu0.5)Si9Al19ON31')|I('Ca–α-sialon')|I('Sr–α-SiAlON:Eu2+')|I('(Sr0.5Eu0.5)Si9Al19ON31')|I('β-sialon:Eu2+')|I('α-sialon:Eu2+')|I('γ-sialon:Eu2+')|I('β-sialon')|I('α-sialon')|I('γ-sialon')|I('YAG:Ce3+')
    | I('Sr1-xEuxSi9Al19ON31') | I('Ba3ScB3O9:Eu2+') | I('CaBa[Li2Al6N8]') | I('Ca2MgSi2O7') |I('Zn2SiO4:Mn2+')|I('Ca/Eu–α-SiAlONs')|R('Li\-α\-SiAlON:Eu2\+')|R('^(Ca|Ba|Sr|Na|K|Rb|Y|Zn|La|Mg|Al|Li|Gd|Cs|Co|Ga|As)?-?(α|γ|β)?-(SiAlON|sialon)s?:?(Eu|Ce|Mn|Tb|Cr)?\d?\+?')
    |R('α\-SrNCN:Eu2\+')|R('Li–a-SiAlON:Eu2+')|R('Sr\-SiAlON:Eu2\+')|I('Eu2+-doped')+I('BaYSi4N7')|ZeroOrMore(R('(Ca|Ba|Sr|Na|K|Rb|Y|Zn|La|Mg|Al|Li|Gd|Cs|Co|Ga|As)')+ hyphen) +ZeroOrMore(R('(α|γ|β|a)')+hyphen)+ R('(SiAlON|sialon)s?')+ZeroOrMore(R(':')+R('(Eu|Ce|Mn|Tb|Cr)?\d?\+?'))
).add_action(join)
Phosphors_name = Group(phosphor_formula_1|phosphor_formula_dop|phosphor_formula2|phosphors)('phosphor')
solvent_formula = (
    W('CCl4') | W('(CH3)2CHOH') | W('CH3NO2') | W('CH3OH') | W('CH3Ph') | W('CH3SOCH3') | W('CHCl2') | W('CHCl3') | W('Cl2CH2') |
    W('ClCH2CH2Cl')
)

# Over-tokenized variants first, useful for matching in tables with fine tokenizer
nmr_solvent = (
    I('THF') + W('-') + I('d8') | I('d8') + W('-') + I('THF') |  I('d2-tetrachloroethane')

)

#: Solvent names.
other_solvent = (
    I('1-butanol') |I('1,1,2,2-tetrachloroethane-d2') 
)
# Potentially problematic solvent names at the end above...

solvent_name_options = (nmr_solvent | solvent_formula | other_solvent)
solvent_name = (Optional(include_prefix) + solvent_name_options)('names').add_action(join).add_action(fix_whitespace)
chemical_name_blacklist = (I('mmc'))
proper_chemical_name_options = Not(chemical_name_blacklist) + (formula)
proper_chemical_name_withcolon = (
    proper_chemical_name_options + doped_ion
)
# Mixtures e.g. 30% mol MnAs + 70% mol ZnGeAs2
mixture_component = (R('\d+(\.\d+)?') + W('%') + Optional(I('mol')) + proper_chemical_name_options).add_action(join)
mixture_phrase = (mixture_component + W('+') + mixture_component).add_action(join)('names')

chemical_name_options = (proper_chemical_name_options| proper_chemical_name_withcolon | mixture_phrase|phosphors+Doped_ion|phosphors ) + ZeroOrMore(joining_characters + (proper_chemical_name_options | mixture_phrase))
#
chemical_name = (chemical_name_options)('names').add_action(join).add_action(fix_whitespace)

# Label phrase structures
# label_type delim? label delim? chemical_name ZeroOrMore(delim cc label delim? chemical_name)

label_name_cem = (chemical_label + optdelim + chemical_name)('compound')
labelled_as = (R('^labell?ed$') + W('as')).hide()
optquote = Optional(quote.hide())

label_before_name = Optional(synthesis_of | to_give) + label_type + optdelim + label_name_cem + ZeroOrMore(optdelim + cc + optdelim + label_name_cem)

likely_abbreviation = (Optional(include_prefix + Optional(hyphen)) + R('^([A-Z]{2,6}(\-[A-Z]{1,6})?|[A-Z](\-[A-Z]{2,6}))$'))('names').add_action(join).add_action(fix_whitespace)

name_with_optional_bracketed_label = (Optional(synthesis_of | to_give) + chemical_name + Optional(lbrct + Optional(labelled_as + optquote) + (chemical_label | lenient_chemical_label | likely_abbreviation) + optquote + rbrct))('compound')

# Lenient name match that should be used with stricter surrounding context
lenient_name = OneOrMore(Not(rbrct) + (bcm | icm | jj | nn | nnp | nns | hyph | cd | ls | W(',')))('names').add_action(join).add_action(fix_whitespace)

# Very lenient name and label match, with format like "name (Compound 3)"
lenient_name_with_bracketed_label = (Start() + Optional(synthesis_of) + lenient_name + lbrct + label_type.hide() + lenient_chemical_label + rbrct)('compound')

# chemical name with a comma in it that hasn't been tagged.
name_with_comma_within = Start() + Group(Optional(synthesis_of) + (cm + W(',') + cm + Not(cm) + Not(I('and')))('names').add_action(join).add_action(fix_whitespace))('compound')
RE_ion = R('(\d(\.\,\d+)?)?(mol|atom|atoms)?%?(A([glmru]|(s\d\.?))|B[ahikr]?|C[adeflmnorsu(\d)]?|D[bsy]|E[rsu]?|F[elmr$]?|G[ade]|H[efgos]|I[rn]?|K[r(\d\.?)]?|(L[airuvn])|M[dgnot]?|N[abdeip(\d\.?)]?|O[s\d.]?|P[abdmotuOr\d]?|R[abefghnuE]?|S[bcegimnr(\d\.?)]?|T[abehil\d]|U(u[opst])|V|Xe|x|Yb?|Z[nr])(2|3|4|5|6|7)\+')
        
all_ion = R('((A([glmru]|(s\d\.?))|B[ahikr]?|C[adeflmnorsu(\d)]?|D[bsy]|E[rsu]?|F[elmr$]?|G[ade]|H[efgos]|I[rn]?|K[r(\d\.?)]?|(L[airuvn])|M[dgnot]?|N[abdeip(\d\.?)]?|O[s\d.]?|P[abdmotuOr\d]?|R[abefghnuE]?|S[bcegimnr(\d\.?)]?|T[abehil\d]|U(u[opst])|V|Xe|x|Yb?|Z[nr])(2|3|4|5|6|7)\+\/?){1,}')
# Chemical name with a doped label after
name_with_doped_label = ((chemical_name + OneOrMore(colon|delim|hyphen| I('with') | I('for') | I('doped')|I('activated')) + ion_symbol)
                         |((ion_symbol|transition_metals|metals) + ZeroOrMore(hyphen|delim)+OneOrMore(I('doped')|I('codoped')|I('activated')|I('with')|I('in')+I('the')|I('in'))+formula)
                         |all_ion+OneOrMore(I('ions')|I('ion')|I('into')|I('doped')|I('codoped')|I('activated')|I('with')|I('in')+I('the')|I('in'))+chemical_name
                         |(chemical_name + doped_ion)|(ion_symbol|transition_metals|metals)+R('[,\/-]?(and)?')+(ion_symbol|transition_metals|metals)+R('[,\/-]?')+R('co\-?doped')+chemical_name
                         |all_ion + OneOrMore(I('doped')|I('codoped')|I('activated')|I('with')|I('in')+I('the')|I('in'))+chemical_name
                         |phosphors|R('(Ce|La|Mn|Tb|Sm|Eu|Gd|Tb|Dy|Ho|Er|Tm|Yb|Lu)(2|3|4|5|6|7)\+\-(doped|activated)')+formula
                         )('compound').add_action(join)

# Chemical name with an informal label after
name_with_informal_label = (chemical_name + Optional(R('compounds?')) + OneOrMore(delim | I('with') | I('for')) + informal_chemical_label)('compound')

# to_give_bracketed_label = to_give + lenient_name  # TODO: Come back to this

# TODO: Currently ensuring roles are captured from text preceding cem/cem_phrase ... abstract out the 'to_give"

cem = (name_with_doped_label |name_with_informal_label |  lenient_name_with_bracketed_label | label_before_name | name_with_comma_within | name_with_optional_bracketed_label)

cem_phrase = Group(cem)('cem_phrase').add_action(fix_whitespace)

r_equals = R('^[R]$') + W('=') + OneOrMore(Not(rbrct) + (bcm | icm | nn | nnp | nns | hyph | cd | ls))
of_table = (I('of') | I('in')) + Optional(dt) + I('table')

bracketed_after_name = Optional(comma) + lbrct + Optional(labelled_as + optquote) + (chemical_label | lenient_chemical_label | likely_abbreviation) + optquote + Optional(Optional(comma) + r_equals | of_table) + rbrct
comma_after_name = comma + Optional(labelled_as + optquote) + (chemical_label | likely_abbreviation)

compound_heading_ending = (Optional(comma) + ((lbrct + (chemical_label | lenient_chemical_label | lenient_name) + Optional(Optional(comma) + r_equals | of_table) + rbrct) | chemical_label) + Optional(R('^[:;]$')).hide() | comma + (chemical_label | lenient_chemical_label)) + Optional(W('.')) + End()

# Section number, to allow at the start of a heading
section_no = Optional(I('stage') | I('step') | I('section') | I('part')) + (T('CD') | R('^\d{1,3}(\.\d{1,3}(\.\d{1,3}(\.\d{1,3})?)?)?$') | (Optional(lbrct) + roman_numeral + rbrct))

compound_heading_style1 = Start() + Optional(section_no.hide()) + Optional(synthesis_of) + OneOrMore(Not(compound_heading_ending) + (bcm | icm | jj | nn | nnp | nns | hyph | sym | cd | ls | W(',')))('names').add_action(join).add_action(fix_whitespace) + compound_heading_ending + End()
compound_heading_style2 = chemical_name + Optional(bracketed_after_name)
compound_heading_style3 = synthesis_of + (lenient_name | chemical_name) + Optional(bracketed_after_name | comma_after_name)  # Possibly redundant?
compound_heading_style4 = label_type + lenient_chemical_label + ZeroOrMore((T('CC') | comma) + lenient_chemical_label) + (lenient_name | chemical_name) + Optional(bracketed_after_name | comma_after_name)
compound_heading_style5 = informal_chemical_label
compound_heading_style6 = doped_chemical_label
#compound_heading_style7 = Group(chemical_name + doped_ion)('name').add_action(join).add_action(fix_whitespace)
# TODO: Capture label type in output

compound_heading_phrase = Group(compound_heading_style6 |compound_heading_style5 | compound_heading_style1 | compound_heading_style2 | compound_heading_style3 | compound_heading_style4 | chemical_label)('compound')

names_only = Group(((chemical_name  
              | likely_abbreviation | name_with_doped_label)))('compound').add_action(join).add_action(fix_whitespace)

labels_only = Group((doped_chemical_label | informal_chemical_label | numeric | R('^([A-Z]\d{1,3})$') | strict_chemical_label))('compound')

roles_only = Group((label_type | synthesis_of | to_give))('compound')

formula_p = (
    R('^(\(?\[?\(?(A([glmru]|(s\d\.?))|B[ahikr]?|C[adeflmnorsu(\d)]?|D[bsy]|E[rsu]?|F[elmr$]?|G[ade]|H[efgos]|I[rn]?|K[r(\d\.?)]?|(L[airuvn])|M[dgnot]?|N[abdeip(\d\.?)]?|O[s\d.]?|P[abdmotuOr\d]?|R[abefghnuE]?|S[bcegimnr(\d\.?)]?|T[abehil\d]|U(u[opst])|V|Xe|x|Yb?|Z[nr])(\)?\]?\)?([\d.]+)?(x?y?\-?\+?\/?[\d.]+\-?\+?\/?x?y?)?(\/)?)){2,}(\+?[δβγ])?'))
Doped_ion = (
             R(':') +(ion_symbol|transition_metals+ion_label) 
)
delim = R('[,:;%\./]$') | W(' ') 
co_doped =(R(':') + RE_ion+ OneOrMore(delim +RE_ion))
concentration = (R(':') +(R('x')|R('y')|R('\d+(\.\,\d+)?'))+(ion_symbol|transition_metals+ion_label)) 
concentration_range = R('\(.*\)$')
#add_content = (R('^\(')+R('(x|y|δ|β|0-9|A-Z).+?\)')+R('\)*'))('add_content').add_action(join)
add_content = (R('\(')+OneOrMore(R('(x|y|δ|β|\d|A-Za-z?)+')+R('(mol|atom|at)*')+R('[\.=≈<>≤%,;/:\+]*'))+R('\)'))('add_content').add_action(join)
add_content.tag = 'add_content'
doped_name = R('((A([glmru]|(s\d\.?))|B[ahikr]?|C[adeflmnorsu(\d)]?|D[bsy]|E[rsu]?|F[elmr$]?|G[ade]|H[efgos]|I[rn]?|K[r(\d\.?)]?|(L[airuvn])|M[dgnot]?|N[abdeip(\d\.?)]?|O[s\d.]?|P[abdmotuOr\d]?|R[abefghnuE]?|S[bcegimnr(\d\.?)]?|T[abehil\d]|U(u[opst])|V|Xe|x|Yb?|Z[nr])(2|3|4|5|6|7)?\+?.(doped|activated|codoped))')
co_dop2 = R('(\d(\.\,\d+)?)?([A-Z][a-z](2|3|4|5|6)\+)')+slash+R('(\d(\.\,\d+)?)?([A-Z][a-z](2|3|4|5|6)\+)')+R('co-doped')        
phosphor = (((formula_p + Doped_ion)|co_dop2 + chemical_name|
            (formula_p + Doped_ion + add_content)|chemical_name+OneOrMore(ZeroOrMore(delim)+RE_ion)|doped_name+formula|
            (formula_p+co_doped)|name_with_doped_label|chemical_name|chemical_name+co_doped|
            (formula_p + concentration))+ZeroOrMore(add_content))('Phosphor').add_action(join)


units = (W('nm')|OneOrMore(T('nm')) |OneOrMore(W('nm'))|OneOrMore(R('(cm−1|cm-1)'))|OneOrMore(I('cm')+R('[--—\-‒–—―−]\d?'))|OneOrMore(W('cm')+R('(-|—)1')))('units').add_action(merge)

value = (R('^\d{3}(\.\,\d+)?$'))('value').add_action(join)

multipeaks = (value + ZeroOrMore((I('and')|delim | hyphen| I('to')) + value) )
peaks = (value + ZeroOrMore((delim | hyphen| I('to')|I('and'))+value))('peaks').add_action(join)
specifier = (I('emission')+R('.*?')+I('nm$')|R('emi(t|tted|tting|ts)')|I('em$')|I('emission')+I('peak')|I('emission')+I('band')|I('emission')+I('bands')|
                                            I('emission')+I('wavelength')|I('PL')+R('spectr(a|um)')|I('show')+I('emission')|I('emissions')+I('centered')+I('at')|
                                            R('sho(w|ws).?emission')|I('emission')+I('spectrum')|I('emission')+I('spectra')|R('band.?maximum')+I('at')|
                                            R('(show|shows|exhibit|exhibits)')+R('(red|green|blue|yellow)')+R('(emission|luminescence)')|I('peak')+I('wavelength')|
                                            I('peak')+I('center')+I('at')|
                                             R('λ')+R('(em|max)')|I('emission')+I('maximum')|I('peaking')+I('at')|R('pea(k|ks|ked)')+I('at')|R('\u03bb')+I('em')|
                                             I('emission')+I('at'))('specifier').add_action(join)

def standardize_role(role):
    """Convert role text into standardized form."""
    role = role.lower()
    if any(c in role for c in {'synthesis', 'give', 'yield', 'afford', 'product', 'preparation of'}):
        return 'product'
    return role

class PhosphorParser(BaseSentenceParser):
    _label = None
    _root_phrase = None

    @property
    def root(self):
        label = self.model.labels.parse_expression('labels')
        label_name_phos = (label + optdelim + Phosphors_name)('phosphor')
        return Group(label_name_phos|phosphor_formula_dop |phosphor_formula_1 |phosphor_formula2 |phosphor_formula | phosphors)('phosphor')
    def interpret(self, result, start, end):
        # TODO: Parse label_type into label model object
        # print(etree.tostring(result))
        for cem_el in result.xpath('./phosphor'):
            c = self.model(
                names=cem_el.xpath('./names/text()'),
                labels=cem_el.xpath('./labels/text()'),
                roles=[standardize_role(r) for r in cem_el.xpath('./roles/text()')]
            )
            c.record_method = self.__class__.__name__
            yield c       

# TODO jm2111, Problems here! The parsers don't have a parse method anymore. Ruins parsing of captions.
class CompoundParser(BaseSentenceParser):
    """Chemical name possibly with an associated label."""
    _label = None
    _root_phrase = None

    @property
    def root(self):
        label = self.model.labels.parse_expression('labels')
        label_name_cem = (label + optdelim + chemical_name)('compound')

        label_before_name = Optional(synthesis_of | to_give) + label_type + optdelim + label_name_cem + ZeroOrMore(optdelim + cc + optdelim + label_name_cem)

        name_with_optional_bracketed_label = (Optional(synthesis_of | to_give) + chemical_name + Optional(lbrct + Optional(labelled_as + optquote) + (label) + optquote + rbrct))('compound')

        # Very lenient name and label match, with format like "name (Compound 3)"
        lenient_name_with_bracketed_label = (Start() + Optional(synthesis_of) + lenient_name + lbrct + label_type.hide() + label + rbrct)('compound')

        # Chemical name with a doped label after
        # name_with_doped_label = (chemical_name + OneOrMore(delim | I('with') | I('for')) + label)('compound')

        # Chemical name with an informal label after
        # name_with_informal_label = (chemical_name + Optional(R('compounds?')) + OneOrMore(delim | I('with') | I('for')) + informal_chemical_label)('compound')
        return Group(name_with_informal_label | name_with_doped_label | lenient_name_with_bracketed_label | label_before_name | name_with_comma_within | name_with_optional_bracketed_label)('cem_phrase')

    def interpret(self, result, start, end):
        # TODO: Parse label_type into label model object
        # print(etree.tostring(result))
        for cem_el in result.xpath('./compound'):
            c = self.model(
                names=cem_el.xpath('./names/text()'),
                labels=cem_el.xpath('./labels/text()'),
                roles=[standardize_role(r) for r in cem_el.xpath('./roles/text()')]
            )
            c.record_method = self.__class__.__name__
            yield c


class ChemicalLabelParser(BaseSentenceParser):
    """Chemical label occurrences with no associated name."""
    _label = None
    _root_phrase = None

    @property
    def root(self):
        label = self.model.labels.parse_expression('labels')
        if self._label is label:
            return self._root_phrase
        self._root_phrase = (chemical_label_phrase | Group(label)('chemical_label_phrase'))
        self._label = label
        return self._root_phrase

    def interpret(self, result, start, end):
        # print(etree.tostring(result))
        roles = [standardize_role(r) for r in result.xpath('./roles/text()')]
        for label in result.xpath('./labels/text()'):
            yield self.model(labels=[label], roles=roles)


class CompoundHeadingParser(BaseSentenceParser):
    """Better matching of abbreviated names in dedicated compound headings."""

    root = compound_heading_phrase

    def interpret(self, result, start, end):
        roles = [standardize_role(r) for r in result.xpath('./roles/text()')]
        labels = result.xpath('./labels/text()')
        if len(labels) > 1:
            for label in labels:
                yield self.model(labels=[label], roles=roles)
            for name in result.xpath('./names/text()'):
                yield self.model(names=[name], roles=roles)
        else:
            yield self.model(
                names=result.xpath('./names/text()'),
                labels=labels,
                roles=roles
            )


class CompoundTableParser(BaseTableParser):
    entities = (cem | chemical_label | lenient_chemical_label) | ((I('Formula') | I('Compound')).add_action(join))('specifier')
    root = OneOrMore(entities + Optional(SkipTo(entities)))('root_phrase')

    @property
    def root(self):
        # is always found, our models currently rely on the compound
        chem_name = (cem | chemical_label | lenient_chemical_label)
        compound_model = self.model
        labels = compound_model.labels.parse_expression('labels')
        entities = [labels]

        specifier = (I('Formula') | I('Compound')).add_action(join)('specifier')
        entities.append(specifier)

        # the optional, user-defined, entities of the model are added, they are tagged with the name of the field
        for field in self.model.fields:
            if field not in ['raw_value', 'raw_units', 'value', 'units', 'error', 'specifier']:
                if self.model.__getattribute__(self.model, field).parse_expression is not None:
                    entities.append(self.model.__getattribute__(self.model, field).parse_expression(field))

        # the chem_name has to be parsed last in order to avoid a conflict with other elements of the model
        entities.append(chem_name)

        # logic for finding all the elements in any order

        combined_entities = entities[0]
        for entity in entities[1:]:
            combined_entities = (combined_entities | entity)
        root_phrase = OneOrMore(combined_entities + Optional(SkipTo(combined_entities)))('root_phrase')
        self._root_phrase = root_phrase
        self._specifier = self.model.specifier
        return root_phrase

    def interpret(self, result, start, end):
        # TODO: Parse label_type into label model object
        if result.xpath('./specifier/text()') and \
        (result.xpath('./names/names/text()') or result.xpath('./labels/text()')):
            c = self.model(
                names=result.xpath('./names/names/text()'),
                labels=result.xpath('./labels/text()'),
                roles=[standardize_role(r) for r in result.xpath('./roles/text()')]
            )
            if c is not None:
                c.record_method = self.__class__.__name__
                yield c
