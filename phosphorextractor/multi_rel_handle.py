from .parse import cem
from .parse.cem import chemical_name, chemical_label,ion_symbol,transition_metals,ion_label,name_with_doped_label
from .parse import R, I, W, Optional, merge, join, OneOrMore, Any, ZeroOrMore, Start
from .relex import ChemicalRelationship
from .model import BaseModel, StringType, ListType, ModelType, Compound,Phosphor
from .parse.common import hyphen
from .get_rel import get_rel,get_rel_fwhm
import re
from .dictionary import Dictionary



class MultiHandle(object):

    def __init__(self, sentence_tokens):
        """Phrase Object

        Class for handling which relations and entities appear in a sentence, the base type used for clustering and generating extraction patterns

        Arguments:
            sentence_tokens {[list} -- The sentence tokens from which to generate the Phrase
            relations {list} -- List of Relation objects to be tagged in the sentence
            prefix_length {int} -- Number of tokens to assign to the prefix
            suffix_length {int} -- Number of tokens to assign to the suffix
        """
        self.relationship = get_rel()
        self.relationship_F = get_rel_fwhm()
        self.dictionary = Dictionary()
        self.sentence_tokens = sentence_tokens  
        self.relations = self.relationship.get_candidates(tokens=self.sentence_tokens.tagged_tokens)       
        self.sub_list = []
        self.prop_list = []
        self.obj_list = []
        self.unit_list = []
        self.exci = []     
        self.classification = None
        
        if sentence_tokens:
            self.create()
    def check_2exci(self,objentity,obj_list_copy,token_list):
        
        removed_entities = []
        inds = obj_list_copy.index(objentity)
        if 0 < inds < len(self.obj_list) - 1:
            next_entity = self.obj_list[inds + 1]
            prev_entity = self.obj_list[inds - 1]
            distance2 = abs(objentity.start - next_entity.start)
            if distance2 < 4 and any(keyword in token_list[objentity.start:next_entity.start] for keyword in ('and', 'or')):
                if objentity not in removed_entities and next_entity not in removed_entities:
                    self.obj_list.remove(objentity)
                    self.obj_list.remove(next_entity)
                    removed_entities.append(objentity)
                    removed_entities.append(next_entity)
                    self.exci = [objentity.text, next_entity.text]

            else:
                if objentity not in removed_entities:
                    self.obj_list.remove(objentity)
                    removed_entities.append(objentity)
                    self.exci.append(objentity.text)

        elif inds == 0:
            next_entity = self.obj_list[inds + 1]
            distance2 = abs(objentity.start - next_entity.start)
            if distance2 < 4 and any(keyword in token_list[objentity.start:next_entity.start] for keyword in ('and', 'or')):
                if objentity not in removed_entities and next_entity not in removed_entities:
                    self.obj_list.remove(objentity)
                    self.obj_list.remove(next_entity)
                    removed_entities.append(objentity)
                    removed_entities.append(next_entity)
                    self.exci = [objentity.text, next_entity.text]
                    
            else:
                if objentity not in removed_entities:
                    self.obj_list.remove(objentity)
                    removed_entities.append(objentity)
                    self.exci.append(objentity.text)

        elif inds == len(self.obj_list) - 1:
            prev_entity = self.obj_list[inds - 1]
            distance1 = abs(objentity.start - prev_entity.start)
            #if distance1 < 4 and 'and' in token_list[prev_entity.start:objentity.start]:
            if distance1 < 4 and any(keyword in token_list[prev_entity.start:objentity.start] for keyword in ('and', 'or')):
                if objentity not in removed_entities and prev_entity not in removed_entities:
                    self.obj_list.remove(objentity)
                    self.obj_list.remove(prev_entity)
                    removed_entities.append(objentity)
                    removed_entities.append(prev_entity)
                    self.exci = [objentity.text, prev_entity.text]  
            else:
                if objentity not in removed_entities:
                    self.obj_list.remove(objentity)
                    removed_entities.append(objentity)
                    self.exci.append(objentity.text)     
        else:
            if objentity not in removed_entities:
                self.obj_list.remove(objentity)
                removed_entities.append(objentity)
                self.exci.append(objentity.text)
                 
        return self.exci
    def check_2other(self,objentity,obj_list_copy,token_list):
        
        removed_entities = []
        inds = obj_list_copy.index(objentity)
        if 0 < inds < len(self.obj_list) - 1:
            next_entity = self.obj_list[inds + 1]
            prev_entity = self.obj_list[inds - 1]
            distance2 = abs(objentity.start - next_entity.start)
            #if distance2 < 4 and 'and' in token_list[objentity.start:next_entity.start]:
            if distance2 < 4 and any(keyword in token_list[objentity.start:next_entity.start] for keyword in ('and', 'or')):
                if objentity not in removed_entities and next_entity not in removed_entities:
                    self.obj_list.remove(objentity)
                    self.obj_list.remove(next_entity)
                    removed_entities.append(objentity)
                    removed_entities.append(next_entity)

            if distance2 < 4:
                if objentity not in removed_entities:
                    self.obj_list.remove(objentity)
                    removed_entities.append(objentity)

        elif inds == 0:
            next_entity = self.obj_list[inds + 1]
            distance2 = abs(objentity.start - next_entity.start)
            if distance2 < 4 and any(keyword in token_list[objentity.start:next_entity.start] for keyword in ('and', 'or')):
                if objentity not in removed_entities and next_entity not in removed_entities:
                    self.obj_list.remove(objentity)
                    self.obj_list.remove(next_entity)
                    removed_entities.append(objentity)
                    removed_entities.append(next_entity)

            else:
                if objentity not in removed_entities:
                    self.obj_list.remove(objentity)
                    removed_entities.append(objentity)
                 
        elif inds == len(self.obj_list) - 1:
            prev_entity = self.obj_list[inds - 1]
            distance1 = abs(objentity.start - prev_entity.start)
            if distance1 < 4 and any(keyword in token_list[prev_entity.start:objentity.start] for keyword in ('and', 'or')):
                if objentity not in removed_entities and prev_entity not in removed_entities:
                    self.obj_list.remove(objentity)
                    self.obj_list.remove(prev_entity)
                    removed_entities.append(objentity)
                    removed_entities.append(prev_entity)
            else:
                if objentity not in removed_entities:
                    self.obj_list.remove(objentity)
                    removed_entities.append(objentity)
                 
        else:
            if objentity not in removed_entities:
                self.obj_list.remove(objentity)
                removed_entities.append(objentity)
        return       
    def create(self):
        """ Create a phrase from known relations"""
        sentence = self.sentence_tokens
        relations = self.relations
        #print(relations)
        entity_counter = {}
        # print("Creating phrase")
        combined_entity_list = []
        for relation in relations:
            #print(relation)
            for entity in relation:
                #print(entity)
                #print("11",entity.text)
                if entity in combined_entity_list:
                    continue
                else:
                    if entity.tag not in entity_counter.keys():
                        entity_counter[entity.tag] = 1
                    else:
                        entity_counter[entity.tag] += 1
                combined_entity_list.append(entity)
        sorted_entity_list = sorted(combined_entity_list, key=lambda t: t.start)
        for entity in sorted_entity_list:
            if entity.tag == 'phosphor':
                if len(entity.text) < 5 and entity.text.endswith('+'):
                    continue
                if len(entity.text) < 3:
                    continue
                else:
                    self.sub_list.append(entity)
            elif entity.tag == 'specifier':
                self.prop_list.append(entity)
            elif entity.tag == 'peaks':
                self.obj_list.append(entity)

        search_prop=[] 
        search_ab = []
        token_list = sentence.raw_tokens      
        ll = self.dictionary.excite
        excite = self.dictionary.excite_suffix
        absorpt =self.dictionary.other
        for l in ll:
            search = re.findall(l,str(sentence))
            if search:
                search_prop.extend(search)
        for a in absorpt:
            search = re.findall(a,str(sentence))
            if search:
                search_ab.extend(search)
        
        if search_prop:
             #print(search_prop)
            obj_list_copy = self.obj_list.copy()
            #print('search_prop:',search_prop)   
            for objentity in obj_list_copy:
                if any(ex in search_prop for ex in excite):
                    #print("ex in search_prop for ex in excite")
                    ex_index = None
                    n = 0
                    for ii in [item for item in search_prop if item not in excite]:
                        #print("item for item in search_prop if item not in excite")    
                        try:
                            #print("now try ex_in")
                            ex_in = token_list.index(ii,n)
                            #print('ex_in:',ex_in)
                            if ex_in is not None:
                                ex_index = ex_in
                                #print('ex_index:',ex_index)
                                if 0< (objentity.start - ex_index ) < 4:
                                    if len(self.obj_list) > 1:
                                        #print("self.obj_list) > 1")
                                        self.exci = self.check_2exci(objentity,obj_list_copy,token_list)
                                        n = ex_in + 1            
                                    else:            
                                        self.obj_list.remove(objentity)

                                        self.exci.append(objentity.text)
                                        n = ex_in + 1
                                   
                                else:
                                    #print("<<fair")
                                    n = ex_in + 1 
                        except ValueError:
                            continue

                else:
                    #print("Now in ex_else")
                    ex_index = None
                    n = 0
                    for ii in search_prop:
                        try:
                            ex_in = token_list.index(ii,n)
                            if ex_in is not None:
                                ex_index = ex_in
                                #print('ex_index:',ex_index)
                                if abs(objentity.start - ex_index ) < 5:
                                    #print("abs(objentity.start - ex_index ) < 5")
                                    if len(self.obj_list) > 1:
                                        #print("len(self.obj_list) > 1")
                                        self.exci = self.check_2exci(objentity,obj_list_copy,token_list)
                                        n = ex_in + 1            
                                    else:            
                                        self.obj_list.remove(objentity)
                                        #length_obj = len(self.obj_list)
                                        self.exci.append(objentity.text)
                                        n = ex_in + 1
                                else:
                                    n = ex_in + 1 
                        except ValueError:
                            continue 
                        #print('ex_index2:',ex_index)    
                     
        # extend dic with excitation peak               
        else:
            self.exci = None 
        if search_ab:
            obj_list_copy = self.obj_list.copy()                    
            for objentity in obj_list_copy:        
                abs_index = None
                n = 0
                for ii in search_ab:   
                    try:                            
                        abs_in = token_list.index(ii,n)
                        #print('abs_in_n:',n)
                        if abs_in is not None:
                            abs_index = abs_in
                            #print('abs:',abs_index)
                            if abs(objentity.start - abs_index ) < 4:
                                if len(self.obj_list) > 1:
                                    self.check_2other(objentity,obj_list_copy,token_list)              
                                    n = abs_in + 1            
                                else:            
                                    self.obj_list.remove(objentity)
                                 
                                    n = abs_in + 1
                            else:
                                n = abs_in + 1                
                    except ValueError:
                        continue
        #print('obj_list',self.obj_list)    
        length_sub = len(self.sub_list)
        length_prop = len(self.prop_list)
        length_obj = len(self.obj_list)        
        #print(entity_counter['phosphor'])        
                          
        if length_sub == length_obj and length_sub == 1:
            self.classification = 'sub_obj'
        elif length_sub == length_obj and length_sub > 1:
            self.classification = 'sub_obj_multi'    
        elif length_sub > length_obj:
            self.classification = 'sub_over_obj'
        elif length_sub < length_obj:
            self.classification = 'sub_less_obj'    
            
        return self.classification
    
class F_Handle(object):

    def __init__(self, sentence_tokens):
        """Phrase Object

        Class for handling which relations and entities appear in a sentence, the base type used for clustering and generating extraction patterns

        Arguments:
            sentence_tokens {[list} -- The sentence tokens from which to generate the Phrase
            relations {list} -- List of Relation objects to be tagged in the sentence
            prefix_length {int} -- Number of tokens to assign to the prefix
            suffix_length {int} -- Number of tokens to assign to the suffix
        """
        
        self.relationship = get_rel_fwhm()
        self.dictionary = Dictionary()
        self.sentence_tokens = sentence_tokens  
        self.relations = self.relationship.get_candidates(tokens=self.sentence_tokens.tagged_tokens)       
        self.sub_list = []
        self.prop_list = []
        self.obj_list = []
        self.unit_list = []
        self.exci = []     
        self.classification = None
        
        if sentence_tokens:
            self.create()    
    def create(self):
        sentence = self.sentence_tokens
        relations = self.relations
        #print(relations)
        entity_counter = {}
        # print("Creating phrase")
        combined_entity_list = []
        for relation in relations:
            #print(relation)
            for entity in relation:
                #print(entity)
                #print("11",entity.text)
                if entity in combined_entity_list:
                    continue
                else:
                    if entity.tag not in entity_counter.keys():
                        entity_counter[entity.tag] = 1
                    else:
                        entity_counter[entity.tag] += 1
                combined_entity_list.append(entity)
        sorted_entity_list = sorted(combined_entity_list, key=lambda t: t.start)
        obj_list_0 = []
        for entity in sorted_entity_list:
            if entity.tag == 'phosphor':
                if len(entity.text) < 5 and entity.text.endswith('+'):
                    continue
                if len(entity.text) < 3:
                    continue
                else:
                    self.sub_list.append(entity)
            elif entity.tag == 'specifier':
                self.prop_list.append(entity)
            elif entity.tag == 'fwhm_value':
                obj_list_0.append(entity)
        for objentity in obj_list_0:
            for propentity in self.prop_list:
                if -4 < propentity.end - objentity.start < 0:
                    self.obj_list.append(objentity)

        length_sub = len(self.sub_list)
        length_prop = len(self.prop_list)
        length_obj = len(self.obj_list)        
        #print(entity_counter['phosphor']) 
        if length_sub == length_obj and length_sub == 1:
            self.classification = 'sub_obj'
        elif length_sub == length_obj and length_sub > 1:
            self.classification = 'sub_obj_multi'    
        elif length_sub > length_obj:
            self.classification = 'sub_over_obj'
        elif length_sub < length_obj:
            self.classification = 'sub_less_obj'    
            
        return self.classification       

        
