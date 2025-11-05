"""
Model classes for physical properties.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import six

from .base import BaseModel, StringType, ListType, ModelType
from .units.temperature import TemperatureModel
from .units.length import LengthModel
from ..parse.cem import CompoundParser,CompoundHeadingParser, ChemicalLabelParser,phosphor,units,peaks,  roles_only,names_only,CompoundTableParser
from ..parse.ir import IrParser
from ..parse.mp_new import MpParser
from ..parse.nmr import NmrParser
from ..parse.tg import TgParser
from ..parse.uvvis import UvvisParser
from ..parse.lumin import ExitationParser, FwhmParser, TqParser, IqeParser, EqeParser, EpParser, MyAutoSentenceParser
from ..parse.phosphor import epParser,Specifier,peaks,units,pc_entities,pc_phrase
from ..parse.elements import R, I, Optional, W, Group, NoMatch, Not
from ..parse.actions import merge, join

from ..model.units.quantity_model import DimensionlessModel
from ..parse.auto import AutoTableParser, AutoSentenceParser
from ..parse.apparatus import ApparatusParser
from ..parse.auto import AutoTableParserOptionalCompound, AutoSentenceParserOptionalCompound

#from material import MaterialParser

log = logging.getLogger(__name__)

class Phosphor(BaseModel):
    phosphor = StringType(contextual = True)
    specifier = StringType()
    peaks = StringType()
    units = StringType()

class Compound(BaseModel):
    
    names = ListType(StringType(), parse_expression=names_only, updatable=True)
  
    labels = ListType(StringType(), parse_expression=NoMatch(), updatable=True)
    roles = ListType(StringType(), parse_expression=roles_only, updatable=True)
   
    
    parsers = [CompoundParser(),CompoundHeadingParser(), ChemicalLabelParser(), CompoundTableParser()]



    def merge(self, other):
        """Merge data from another Compound into this Compound."""
        log.debug('Merging: %s and %s' % (self.serialize(), other.serialize()))
        for k in self.keys():
            for new_item in other[k]:
                if new_item not in self[k]:
                    self[k].append(new_item)
        log.debug('Result: %s' % self.serialize())
        return self

    @property
    def is_unidentified(self):
        if not self.names and not self.labels:
            return True
        return False

    @property
    def is_id_only(self):
        """Return True if identifier information only."""
        for key, value in self.items():
            if key not in {'names', 'labels', 'roles'} and value:
                return False
        if self.names or self.labels:
            return True
        return False

    @classmethod
    def update(cls, definitions, strict=True):
        """Update the Compound labels parse expression

        Arguments:
            definitions {list} -- list of definitions found in this element
        """
        log.debug("Updating Compound")
        for definition in definitions:
            label = definition['label']
            if strict:
                new_label_expression = Group(W(label)('labels'))
            else:
                new_label_expression = Group(I(label)('labels'))
            if not cls.labels.parse_expression:
                cls.labels.parse_expression = new_label_expression
            else:
                cls.labels.parse_expression = cls.labels.parse_expression | new_label_expression
        return

    def construct_label_expression(self, label):
        return W(label)('labels')


class Ep(BaseModel):
    compound = ModelType(Compound, required=True, contextual=True, binding=True, updatable=False)
    #phosphors = ListType(ModelType(Phosphor))
    specifier_peak = (Not(I('absorption'))+(I('emission')+R('.*?')+I('nm$')|R('emi(t|tted|tting|ts)')|I('em$')|I('emission')+I('peak')|I('emission')+I('band')|I('emission')+I('bands')|
                                            I('emission')+I('wavelength')|I('PL')+R('spectr(a|um)')|I('show')+I('emission')|I('emissions')+I('centered')+I('at')|
                                            R('sho(w|ws).?emission')|I('emission')+I('spectrum')|I('emission')+I('spectra')|R('band.?maximum')+I('at')|
                                            R('(show|shows|exhibit|exhibits)')+R('(red|green|blue|yellow)')+R('(emission|luminescence)')|I('peak')+I('wavelength')|
                                            I('peak')+I('center')+I('at')|
                                             R('λ')+R('(em|max)')|I('emission')+I('maximum')|I('peaking')+I('at')|
                                             #R('pea(k|ks|ked)')+I('at')|
                                             R('\u03bb')+I('em')|
                                             I('emission')+I('at')))('specifier').add_action(join)
    specifier = StringType(parse_expression=specifier_peak,
                                             required=True, contextual=False, updatable=True)
    ##emission_peak = StringType(parse_expression=(R('(^[0-9]{3}$)')),required=True, contextual=True, updatable=True)
    phosphors = ListType(StringType(),parse_expression=phosphor,required=True,updatable=True)
    emission_peak = ListType(StringType(),parse_expression=peaks,required=True,contextual=True, updatable=True)
    unit = StringType(parse_expression=units,required=True,contextual=False)
    #parsers = [AutoSentenceParser(), AutoTableParserOptionalCompound(), AutoSentenceParserOptionalCompound(),MyAutoSentenceParser()]
    #(R('(\d+{3})\s*(nm|cm)') | R('(\d+{3})\s*(?=[^a-zA-Z])'))
class Fwhm(BaseModel):
    compound = ModelType(Compound, required=True, contextual=True, binding=True, updatable=False)
    specifier = StringType(parse_expression=(I('FWHM') | R('full')+R('width')+R('at')+R('half')+R('maximum')), required=True, contextual=True, updatable=True)
    phosphors = ListType(StringType(),parse_expression=phosphor,required=True,updatable=True)
    fwhm_value = StringType(parse_expression=R('^\d{2,3}(\.\,?\d+)?$'),required=True, contextual=True, updatable=True)
    unit = StringType(parse_expression=units,required=True,contextual=False)
    parsers = [AutoSentenceParser(), AutoTableParserOptionalCompound(), AutoSentenceParserOptionalCompound(),
               MyAutoSentenceParser()]    
    
excitation= (R('excitation') + R('spectrum')+R('in.*?range') + R('(of|between)') | R('excitation') + R('spectrum') + R('cover.*?from'))('excitation')
excvalue = (R('\d{3}') + Optional(R('nm'))+R('(and|to|-)')+R('\d{3}')+Optional(R('nm')))('excvalue')
excitation_spectrum = (excitation + excvalue)

emission = (
        R('emission.*?peak.*?at')+Optional(R('about'))|
     (R('emission.*?maximum.*?at')+Optional(R('about')))|
     (R('emission.*?at')+Optional(R('about')))|
     R('peak.centred.at')|R('peaks.located.at')|R('peaks.situated.at.about')
    )('emission').hide()

emivalue = R('^\d{3,4}(\.\d+)?.*?$')('emivalue')
Units = (R('nm'))('Units')
ep = (emission + emivalue + Units)
exc_specifier = (I('excited') | I('excitation'))
exc_prefix = (Optional(I('the')|I('its')|I('an')).hide()
              +exc_specifier
              +Optional(I('spectrum')|I('band')).hide()
              +Optional((I('exhibit(s|ed)')+I('an')+I('absorption'))|I('was')+I('measured')|I('is')+I('measured')).hide()
              +Optional(I('in')+I('the')+I('range')+I('(of|between)')).hide()
              +Optional(I('covering')+I('from')).hide()
              )
#def relation_import():
 #   from ..relationship import ChemicalRelationship
  #  return ChemicalRelationship(pc_entities,pc_phrase,name='emission_peak')
Specifiers = (I('emission')+R('.*?')+I('nm$')|I('emi(t|tted|tting|ts)')|I('em$')|I('emission')+I('peak')|
                                             R('λ')+I('em')|I('emission')+I('ma(x|xmium)')|I('peak(s|ing).*?at')|R('\u03bb')+I('em')|
                                             I('emission')+I('at'))('specifier').add_action(join)

    #compound = ModelType(Compound)
    #specifier = StringType(parse_expression=(I('emission')+R('.*?')+I('nm$')|I('emi(t|tted|tting|ts)')|I('em$')|I('emission')+I('peak')|
    #                                         R('λ')+I('em')|I('emission')+I('ma(x|xmium)')|I('peak(s|ing).*?at')|R('\u03bb')+I('em')|
    #                                         I('emission')+I('at')),required=True,contextual = True,updatable=True)
    #phosphor = ListType(StringType(parse_expression=phosphor,required=True,contextual = True,updatable=True))
    #specifier = StringType(parse_expression=specifier)
    #value = StringType(parse_expression=(R('(^[0-9]{3}$)')),required=True,contextual = True,updatable=True)
    #units = StringType(parse_expression=units)
    #parsers = [AutoSentenceParser(), AutoTableParserOptionalCompound(), AutoSentenceParserOptionalCompound(),MyAutoSentenceParser()]
    
class Excspectrum(BaseModel):
    exc_specifier = (I('excited') | I('excitation') | I('excitable'))
    exc_prefix = (Optional(I('the')|I('its')|I('an')).hide()
              +exc_specifier
              +Optional(I('spectrum')|I('band')|I('peak')).hide()
              +Optional((I('exhibit(s|ed)')+I('an')+I('absorption'))|I('was')+I('(measured|found)')|I('is')+I('(measured|found)d')).hide()
              +Optional(I('in')+I('the')+I('range')+I('(of|between)')).hide()
              +Optional(I('at')).hide()
              +Optional(I('covering')+I('from')).hide()
              )
    compound = ModelType(Compound)
    specifier = StringType(parse_expression=(I('excited') | I('excitation')| I('excitable')), required=True, contextual=True, updatable=True)
    exc_prefix_ = StringType(parse_expression=exc_prefix, required=True, contextual=False, updatable=True)
    excited_value = StringType(parse_expression=((R('([0-9]{3}$)')|R('(\d+(\.\d+)?)\s*(nm|cm)') | 
                                                 R('(\d+(\.\d+)?)\s*(?=[^a-zA-Z])'))),
                               required=True, contextual=True, updatable=True)
    parsers = [AutoSentenceParser(), AutoTableParserOptionalCompound(), AutoSentenceParserOptionalCompound(),
               MyAutoSentenceParser(), ExitationParser()]





class Tq(BaseModel):
    compound = ModelType(Compound)
    specifier = StringType(parse_expression=I('thermal') + R('quen(ch|ched|ching)')+I('temperature') | I('TQ') , required=True,
                           contextual=True, updatable=True)
    tq_value = StringType(parse_expression=(R('^[0-9]{1,3}%$')),
                            required=True, contextual=True, updatable=True)
    parsers = [AutoSentenceParser(), AutoTableParserOptionalCompound(), AutoSentenceParserOptionalCompound(),
               MyAutoSentenceParser(), TqParser()]
#(I('quen(ch|ching)') | I('^150') | I('initial') + I('intensity')| I('TQ') | I('initial')).add_action(join)
class Iqe(BaseModel):
    compound = ModelType(Compound)
    specifier = StringType(parse_expression=I('quantum')+I('effienc(y|ies)')|I('IQ(Y|E)')|I('internal')+I('Q(Y|E)'),required=True,
                           contextual=True, updatable=True)
    IQE = StringType(parse_expression=R('[0-9]{1,3}%$'),contextual=True)
    iqevalue = StringType(contextual=True)
    parsers = [IqeParser()]

class Eqe(BaseModel):
    EQE = StringType(contextual=True)
    eqevalue = StringType(contextual=True)
    parsers = [EqeParser()]

class Apparatus(BaseModel):
    name = StringType()
    parsers = [ApparatusParser()]


class UvvisPeak(BaseModel):
    #: Peak value, i.e. wavelength
    value = StringType()
    #: Peak value units
    units = StringType(contextual=True)
    # Extinction value
    extinction = StringType()
    # Extinction units
    extinction_units = StringType(contextual=True)
    # Peak shape information (e.g. shoulder, broad)
    shape = StringType()


class UvvisSpectrum(BaseModel):
    solvent = StringType(contextual=True)
    temperature = StringType(contextual=True)
    temperature_units = StringType(contextual=True)
    concentration = StringType(contextual=True)
    concentration_units = StringType(contextual=True)
    apparatus = ModelType(Apparatus, contextual=True)
    peaks = ListType(ModelType(UvvisPeak))
    compound = ModelType(Compound)
    parsers = [UvvisParser()]


class IrPeak(BaseModel):
    value = StringType()
    units = StringType(contextual=True)
    strength = StringType()
    bond = StringType()


class IrSpectrum(BaseModel):
    solvent = StringType(contextual=True)
    temperature = StringType(contextual=True)
    temperature_units = StringType(contextual=True)
    concentration = StringType(contextual=True)
    concentration_units = StringType(contextual=True)
    apparatus = ModelType(Apparatus, contextual=True)
    peaks = ListType(ModelType(IrPeak))
    compound = ModelType(Compound)
    parsers = [IrParser()]


class NmrPeak(BaseModel):
    shift = StringType()
    intensity = StringType()
    multiplicity = StringType()
    coupling = StringType()
    coupling_units = StringType(contextual=True)
    number = StringType()
    assignment = StringType()


class NmrSpectrum(BaseModel):
    nucleus = StringType(contextual=True)
    solvent = StringType(contextual=True)
    frequency = StringType(contextual=True)
    frequency_units = StringType(contextual=True)
    standard = StringType(contextual=True)
    temperature = StringType(contextual=True)
    temperature_units = StringType(contextual=True)
    concentration = StringType(contextual=True)
    concentration_units = StringType(contextual=True)
    apparatus = ModelType(Apparatus, contextual=True)
    peaks = ListType(ModelType(NmrPeak))
    compound = ModelType(Compound)
    parsers = [NmrParser()]

class MeltingPoint(TemperatureModel):
    solvent = StringType(contextual=True)
    concentration = StringType(contextual=True)
    concentration_units = StringType(contextual=True)
    apparatus = ModelType(Apparatus, contextual=True)
    compound = ModelType(Compound, contextual=True)
    parsers = [MpParser()]


class GlassTransition(BaseModel):
    """A glass transition temperature."""
    value = StringType()
    units = StringType(contextual=True)
    method = StringType(contextual=True)
    concentration = StringType(contextual=True)
    concentration_units = StringType(contextual=True)
    compound = ModelType(Compound)
    parsers = [TgParser()]


class QuantumYield(BaseModel):
    """A quantum yield measurement."""
    value = StringType()
    units = StringType(contextual=True)
    solvent = StringType(contextual=True)
    type = StringType(contextual=True)
    standard = StringType(contextual=True)
    standard_value = StringType(contextual=True)
    standard_solvent = StringType(contextual=True)
    concentration = StringType(contextual=True)
    concentration_units = StringType(contextual=True)
    temperature = StringType(contextual=True)
    temperature_units = StringType(contextual=True)
    apparatus = ModelType(Apparatus, contextual=True)


class FluorescenceLifetime(BaseModel):
    """A fluorescence lifetime measurement."""
    value = StringType()
    units = StringType(contextual=True)
    solvent = StringType(contextual=True)
    concentration = StringType(contextual=True)
    concentration_units = StringType(contextual=True)
    temperature = StringType(contextual=True)
    temperature_units = StringType(contextual=True)
    apparatus = ModelType(Apparatus, contextual=True)


class ElectrochemicalPotential(BaseModel):
    """An oxidation or reduction potential, from cyclic voltammetry."""
    value = StringType()
    units = StringType(contextual=True)
    type = StringType(contextual=True)
    solvent = StringType(contextual=True)
    concentration = StringType(contextual=True)
    concentration_units = StringType(contextual=True)
    temperature = StringType(contextual=True)
    temperature_units = StringType(contextual=True)
    apparatus = ModelType(Apparatus, contextual=True)

class NeelTemperature(TemperatureModel):
    # expression = (I('T')+I('N')).add_action(merge)
    expression = I('TN')
    # specifier = I('TN')
    specifier = StringType(parse_expression=expression, required=True, contextual=False, updatable=False)
    compound = ModelType(Compound, required=False, contextual=False)


class CurieTemperature(TemperatureModel):
    # expression = (I('T') + I('C')).add_action(merge)
    expression = ((I('Curie') + R('^temperature(s)?$')) |  R('T[Cc]\d?')).add_action(join)
    specifier = StringType(parse_expression=expression, required=True, contextual=False, updatable=False)
    compound = ModelType(Compound, required=False, contextual=False)


class InteratomicDistance(LengthModel):
    specifier_expression = (R('^bond$') + R('^distance')).add_action(merge)
    specifier = StringType(parse_expression=specifier_expression, required=False, contextual=True)
    rij_label = R('^((X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr)\-?(X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr))$')
    species = StringType(parse_expression=rij_label, required=True, contextual=False)
    compound = ModelType(Compound, required=True, contextual=True)
    another_label = StringType(parse_expression=R('^adgahg$'), required=False, contextual=False)


class CoordinationNumber(DimensionlessModel):
    # something like NTi-O will not work with this, only work if there is space between the label and specifier
    coordination_number_label = R('^((X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr)\-?(X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr))$')
    # specifier = (R('^(N|n|k)$') | (I('Pair') + I('ij')).add_action(merge)
    specifier_expression = R('^(N|n|k)$')
    specifier = StringType(parse_expression=specifier_expression, required=True, contextual=True)

    cn_label = StringType(parse_expression=coordination_number_label, required=True, contextual=True)
    compound = ModelType(Compound, required=True, contextual=True)


class CNLabel(BaseModel):
    # separate model to test automated parsing for stuff that are not quantities
    coordination_number_label = R('^((X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr)\-?(X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr))$')
    specifier = (I('Pair') + I('ij')).add_action(merge)
    label_Juraj = StringType(parse_expression=coordination_number_label)
    compound = ModelType(Compound, required=False)
    parsers = [AutoSentenceParser(), AutoTableParser()]

