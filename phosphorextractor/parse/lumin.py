from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import re


from chemdataextractor.parse.common import hyphen
from chemdataextractor.parse.base import BaseSentenceParser
from chemdataextractor.utils import first
from chemdataextractor.parse.actions import strip_stop
from chemdataextractor.parse.elements import W, I, T, R, Optional, ZeroOrMore, OneOrMore
from chemdataextractor.parse.cem import chemical_name
from chemdataextractor.model import BaseModel
from chemdataextractor.parse.auto import AutoSentenceParser
from chemdataextractor.parse.actions import merge, join
log = logging.getLogger(__name__)

#激发波段parser
excitation= (R('excitation') + R('spectrum')+R('in.*?range') + R('(of|between)') | R('excitation') + R('spectrum') + R('cover.*?from'))('excitation')
excvalue = (R('\d{3}') + Optional(R('nm'))+R('(and|to|-)')+R('\d{3}')+Optional(R('nm')))('excvalue')
excitation_spectrum = (excitation + excvalue)

class ExitationParser(BaseSentenceParser):
    root = excitation_spectrum

    def interpret(self, result, start, end):
        c = self.model.fields['compound'].model_class()
        exc = self.model(
            excitation=first(result.xpath('./excitation/text()')),
            excvalue=first(result.xpath('./excvalue/value/text()'))
        )
        exc.compound = c
        yield c


#发射波峰
emission = (
        R('emission.*?peak.*?at')+Optional(R('about'))|
     (R('emission.*?maximum.*?at')+Optional(R('about')))|
     (R('emission.*?at')+Optional(R('about')))
    )('emission').hide()

emivalue = R('^\d{3,4}(\.\d+)?.*?$')('emivalue')
Units = (R('nm'))('Units')
ep = (emission + emivalue + Units)
class EpParser():
    root = ep
    def interpret(self,result,start,end):
        c = self.model.fields['compound'].model_class()
        f = self.model(
        emission = first(result.xpath('./emission/text()')),
            emivalue = first(result.xpath('./emivalue/text()')),
            Units = first(result.xpath('./Units/text()'))
        )
        f.compound = c
        yield c
class MyAutoSentenceParser(AutoSentenceParser):
    root = (
                R('emission') +
                Optional(I('peak')) +
                Optional(I('centred')) +
                Optional(W(':')).hide() +
                Optional(I('maxim(um|a)')) +
                Optional(R('at')) +
                Optional(I('approximately')).hide() +
                Optional(I('around'))
        ).add_action(merge)
    def interpret(self,result,start,end):
        c = self.model.fields['compound'].model_class()
        f = self.model(
        emission_peak=first(result.xpath('./emission_peak/text()')),
        )
        f.compound = c
        yield c
#半高宽parser
FWHM =((I('full') + R('width')+R('at')+R('half')+R('maximum') + Optional(I('FWHM'))+Optional(R('[)(]'))+Optional(R('='))|I('FWHM')+Optional(R('[)(]'))+Optional(R('='))+Optional(R('of'))|R('band')+R('width')+Optional(R('of'))+Optional(R('is')))('FWHM')).hide()
fwhmvalue = (R('\d+(\.\d+)?$'))('fwhmvalue')
units = (R('nm')|R('cm-1'))('units')
fwhm = (FWHM + fwhmvalue + units)

class FwhmParser():
    root = fwhm
    def interpret(self, result, start, end):
        c = self.model.fields['compound'].model_class()
        f = self.model(
            FWHM=first(result.xpath('./FWHM/text()')),
            units = first(result.xpath('./units/text()')),
            fwhmvalue = first(result.xpath('./fwhmvalue/text()'))

        )
        f.compound = c
        yield c


#热猝灭温度parser
tqprefix = (
                I('at.*150') + R('°') + R('C') + Optional(R('drops.*to')) + Optional(R('(maintain|retain).*about')) |
                Optional(R('(loss|decrease)')) + Optional(R('(of|in)')) + Optional(R('(emission|luminescence)')) + R(
            'intensity') + R('(is|was)') + Optional(R('only')))('tqprefix')

tqsuffix = (
            R('of') + R('the') + Optional(R('initial')) + R('intensity') |
                Optional(R('(loss|decrease)')) + Optional(R('(of|in)')) + Optional(R('(emission|luminescence)')) + R(
            'intensity') + Optional(R('at') + R('150') + R('°C')))('tqsuffix')
tqvalue = (R('\d{1,3}%$'))('tqvalue')
TQ = (tqprefix + tqvalue + tqsuffix)

class TqParser():
    root = TQ
    def interpret(self, result, start, end):
            c = self.model.fields['compound'].model_class()
            f = self.model(
                tqprefix=first(result.xpath('./tqprefix/text()')),
                tqvalue = first(result.xpath('./tqvalue/text()')),
                tqsuffix = first(result.xpath('./tqsuffix/text()'))

            )
            f.compound = c
            yield c



#IQE
IQE = (I('internal') + Optional(R('quantum')) + R('efficienc.*(are|was|at)') + Optional(R('in')+R('the')+R('range')+R('of')) |
       I('IQ[YE].*(are|was|at)') |
       I('internal')+I('QE.*?(are|was|at|is)') +
       Optional(R('about')))('IQE')

iqevalue = (R('\d{1,3}.*%'))('iqevalue')
iqe = (IQE + iqevalue)
class IqeParser():
    root = iqe
    def interpret(self, result, start, end):
        c = self.model.fields['compound'].model_class()
        f = self.model(
            IQE = first(result.xpath('./IQE/text()')),
            iqevalue = first(result.xpath('./iqevalue/text()'))
        )
        f.compound = c
        yield c

#EQE parser
EQE = (I('external') + Optional(R('quantum'))+R('efficienc.*?(are|was|at)')|I('external')+I('QE.*?(are|was|at|is)') +Optional(R('about')))('EQE')
eqevalue = (R('\d{1,3}.*?%'))('eqevalue')
eqe = (EQE+eqevalue)
class EqeParser():
    root = eqe
    def interpret(self, result, start, end):
        c = self.model.fields['compound'].model_class()
        f = self.model(
            EQE = first(result.xpath('./EQE/text()')),
            eqevalue = first(result.xpath('./eqevalue/text()'))
        )
        f.compound = c
        yield c