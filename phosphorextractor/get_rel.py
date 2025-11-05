from .parse.cem import chemical_name, chemical_label,ion_symbol,transition_metals,ion_label,name_with_doped_label,transition_element,metals
from .parse import R, I, W, Optional, merge, join, OneOrMore, Any, ZeroOrMore, Start
from .parse.elements import Not
from .relex import ChemicalRelationship
from .model import BaseModel, StringType, ListType, ModelType, Compound,Phosphor
from .parse.common import hyphen,slash,percent

def get_rel():
        #Compound.EPEAK = ModelType(Phosphor)   
        specifier = (Not(I('absorption'))+(I('emission')+R('.*?')+I('nm$')|R('emi(t|tted|tting|ts)')|I('em$')|I('emission')+I('peak')|I('emission')+I('band')|I('emission')+I('bands')|
                                                    I('emission')+I('wavelength')|I('PL')+R('spectr(a|um)')|I('show')+I('emission')|I('emissions')+I('centered')+I('at')|
                                                    R('sho(w|ws).?emission')|I('emission')+I('spectrum')|I('emission')+I('spectra')|R('band.?maximum')+I('at')|
                                                    R('(show|shows|exhibit|exhibits)')+R('(red|green|blue|yellow)')+R('(emission|luminescence)')|I('peak')+I('wavelength')|
                                                    I('peak')+I('center')+I('at')|
                                                    R('λ')+R('(em|max)')|I('emission')+I('maximum')|
                                                    #R('pea(k|ks|ked)')+I('at')|
                                                    R('\u03bb')+I('em')|
                                                    I('emission')+I('at')))('specifier').add_action(join)
        delim = R('[-_@%,~:;\./]$') | W(' ') 
        RE_ion = R('(\d(\.\,?\d+)?)?(mol|atom|atoms)?(A([glmru]|(s\d\.?))|B[ahikr]?|C[adeflmnorsu(\d)]?|D[bsy]|E[rsu]?|F[elmr$]?|G[ade]|H[efgos]|I[rn]?|K[r(\d\.?)]?|(L[airuvn])|M[dgnot]?|N[abdeip(\d\.?)]?|O[s\d.]?|P[abdmotuOr\d]?|R[abefghnuE]?|S[bcegimnr(\d\.?)]?|T[abehmil\d]|U(u[opst])|V|Xe|x|Yb?|Z[nr])(2|3|4|5|6|7)\+')
        specifier.tag = 'specifier'
        units = (W('nm'))('units').add_action(merge)
        units.tag = 'units'
        value = (R('^\d{3,4}(\.\,?\d+)?$'))('value').add_action(join)
        value.tag = 'value'
        #multipeaks = (value + ZeroOrMore((I('and')|delim | hyphen| I('to')) + value) )
        peaks = (value + ZeroOrMore((delim | hyphen| I('to')|I('and'))+value)+ZeroOrMore(delim + I('and') + value))('peaks').add_action(join)
        peaks.tag = 'peaks'
        formula = (
            R('^(\(?\[?\(?(A([glmru]|(s\d\.?))|B[ahikr]?|C[adeflmnorsu(\d)]?|D[bsy]|E[rsu]?|F[elmr$]?|G[ade]|H[efgos]|I[rn]?|K[r(\d\.?)]?|(L[airuvn])|M[dgnot]?|N[abdeip(\d\.?)]?|O[s\d.]?|P[abdmotuOr\d]?|R[abefghnuE]?|S[bcegimnr(\d\.?)]?|T[abehil\d]|U(u[opst])|V|Xe|x|Yb?|Z[nr])(\)?\]?\)?([\d.]+)?(x?y?\-?\+?\/?[\d.]+\-?\+?\/?x?y?)?(\/)?)){2,}(\+?[δβγ])?'))
        Doped_ion = (R(':') +ZeroOrMore(R('\d+(\.\,\d+)?'))+(ion_symbol|transition_metals+ion_label|transition_element|metals))
        #Doped_ion = R(':') + RE_ion
        
        co_doped =(R(':') + RE_ion+ OneOrMore(delim +RE_ion))
        co_dop2 = R('(\d(\.\,\d+)?)?([A-Z][a-z](2|3|4|5|6)\+)')+slash+R('(\d(\.\,\d+)?)?([A-Z][a-z](2|3|4|5|6)\+)')+ZeroOrMore(R('(ions|into|in)'))+R('(co-doped|doped|coactivated|codoped)')
        concentration = (R(':') +(R('x')|R('y')|R('\d+(\.\,\d+)?'))+(ion_symbol|transition_metals+ion_label))  
        #concentration_range = R('\(.*\)$')
        #add_content = (R('^\(')+R('(x|y|δ|β|0-9|A-Z).+?\)')+R('\)*'))('add_content').add_action(join)
        add_content = (R('\(')+OneOrMore(R('(x|y|δ|β|(\d+(\.\,\d+)?)|A-Za-z?)+')+ZeroOrMore(R('(mol|atom|at)*'))+ZeroOrMore(R('[\.=≈<>≤%,;/:\+]*')))+R('\)'))('add_content').add_action(join)
        add_content.tag = 'add_content'
        doped_name = R('((A([glmru]|(s\d\.?))|B[ahikr]?|C[adeflmnorsu(\d)]?|D[bsy]|E[rsu]?|F[elmr$]?|G[ade]|H[efgos]|I[rn]?|K[r(\d\.?)]?|(L[airuvn])|M[dgnot]?|N[abdeip(\d\.?)]?|O[s\d.]?|P[abdmotuOr\d]?|R[abefghnuE]?|S[bcegimnr(\d\.?)]?|T[abehil\d]|U(u[opst])|V|Xe|x|Yb?|Z[nr])(2|3|4|5|6|7)?\+?.(doped|activated|codoped))')
        mol = R(':') + R('(\d(\.\,\d+)?)?') + R('(mol|atom|atoms)') + R('%')
        mol_second = R('(\d(\.\,\d+)?)?') + R('(mol|atom|atoms)') + R('%') + RE_ion
        phosphor = (((formula + Doped_ion)|chemical_name+OneOrMore(ZeroOrMore(delim)+RE_ion)|formula+mol+RE_ion+ZeroOrMore(delim+mol_second)|co_dop2+chemical_name|doped_name+formula|(formula + Doped_ion + add_content)|(formula+co_doped)|chemical_name+co_doped|name_with_doped_label|chemical_name|(formula + concentration))+ZeroOrMore(add_content))('phosphor').add_action(join)
        #|chemical_name|name_with_doped_label|(formula + concentration)
        phosphor.tag = 'phosphor'
        entities = (phosphor|specifier|peaks+units)
        pc_phrase = (entities + OneOrMore(entities | Any()))('EPEAKs')
        pc_entities = [phosphor,specifier,peaks,units]
        relationship = ChemicalRelationship(pc_entities,pc_phrase,name='EPEAK')
        return relationship

def get_rel_fwhm():
        specifier = (I('FWHM')|R('full')+R('width')+R('at')+R('half')+R('maximum'))('specifier').add_action(join)
        delim = R('[-_@%,~:;\./]$') | W(' ') 
        RE_ion = R('(\d(\.\,?\d+)?)?(mol|atom|atoms)?(A([glmru]|(s\d\.?))|B[ahikr]?|C[adeflmnorsu(\d)]?|D[bsy]|E[rsu]?|F[elmr$]?|G[ade]|H[efgos]|I[rn]?|K[r(\d\.?)]?|(L[airuvn])|M[dgnot]?|N[abdeip(\d\.?)]?|O[s\d.]?|P[abdmotuOr\d]?|R[abefghnuE]?|S[bcegimnr(\d\.?)]?|T[abehmil\d]|U(u[opst])|V|Xe|x|Yb?|Z[nr])(2|3|4|5|6|7)\+')
        specifier.tag = 'specifier'
        units = (W('nm'))('units').add_action(merge)
        units.tag = 'units'
        fwhm_value = (R('^\d{2,3}(\.\,?\d+)?$'))('fwhm_value').add_action(join)
        fwhm_value.tag = 'fwhm_value'
        formula = (
            R('^(\(?\[?\(?(A([glmru]|(s\d\.?))|B[ahikr]?|C[adeflmnorsu(\d)]?|D[bsy]|E[rsu]?|F[elmr$]?|G[ade]|H[efgos]|I[rn]?|K[r(\d\.?)]?|(L[airuvn])|M[dgnot]?|N[abdeip(\d\.?)]?|O[s\d.]?|P[abdmotuOr\d]?|R[abefghnuE]?|S[bcegimnr(\d\.?)]?|T[abehil\d]|U(u[opst])|V|Xe|x|Yb?|Z[nr])(\)?\]?\)?([\d.]+)?(x?y?\-?\+?\/?[\d.]+\-?\+?\/?x?y?)?(\/)?)){2,}(\+?[δβγ])?'))
        Doped_ion = (R(':') +ZeroOrMore(R('\d+(\.\,\d+)?'))+(ion_symbol|transition_metals+ion_label|transition_element|metals))
  
        co_doped =(R(':') + RE_ion+ OneOrMore(delim +RE_ion))
        co_dop2 = R('(\d(\.\,\d+)?)?([A-Z][a-z](2|3|4|5|6)\+)')+slash+R('(\d(\.\,\d+)?)?([A-Z][a-z](2|3|4|5|6)\+)')+ZeroOrMore(R('(ions|into|in)'))+R('(co-doped|doped|coactivated|codoped)')
        concentration = (R(':') +(R('x')|R('y')|R('\d+(\.\,\d+)?'))+(ion_symbol|transition_metals+ion_label))  
        #add_content = (R('^\(')+R('(x|y|δ|β|0-9|A-Z).+?\)')+R('\)*'))('add_content').add_action(join)
        add_content = (R('\(')+OneOrMore(R('(x|y|δ|β|(\d+(\.\,\d+)?)|A-Za-z?)+')+ZeroOrMore(R('(mol|atom|at)*'))+ZeroOrMore(R('[\.=≈<>≤%,;/:\+]*')))+R('\)'))('add_content').add_action(join)
        add_content.tag = 'add_content'
        doped_name = R('((A([glmru]|(s\d\.?))|B[ahikr]?|C[adeflmnorsu(\d)]?|D[bsy]|E[rsu]?|F[elmr$]?|G[ade]|H[efgos]|I[rn]?|K[r(\d\.?)]?|(L[airuvn])|M[dgnot]?|N[abdeip(\d\.?)]?|O[s\d.]?|P[abdmotuOr\d]?|R[abefghnuE]?|S[bcegimnr(\d\.?)]?|T[abehil\d]|U(u[opst])|V|Xe|x|Yb?|Z[nr])(2|3|4|5|6|7)?\+?.(doped|activated|codoped))')
        mol = R(':') + R('(\d(\.\,\d+)?)?') + R('(mol|atom|atoms)') + R('%')
        mol_second = R('(\d(\.\,\d+)?)?') + R('(mol|atom|atoms)') + R('%') + RE_ion
        phosphor = (((formula + Doped_ion)|chemical_name+OneOrMore(ZeroOrMore(delim)+RE_ion)|formula+mol+RE_ion+ZeroOrMore(delim+mol_second)|co_dop2+chemical_name|doped_name+formula|(formula + Doped_ion + add_content)|(formula+co_doped)|chemical_name+co_doped|name_with_doped_label|chemical_name|(formula + concentration))+ZeroOrMore(add_content))('phosphor').add_action(join)
      
        phosphor.tag = 'phosphor'
        entities = (phosphor|specifier|fwhm_value+units)
        pc_phrase = (entities + OneOrMore(entities | Any()))('Fwhms')
        pc_entities = [phosphor,specifier,fwhm_value,units]
        relationship_F = ChemicalRelationship(pc_entities,pc_phrase,name='Fwhm')
        return relationship_F


