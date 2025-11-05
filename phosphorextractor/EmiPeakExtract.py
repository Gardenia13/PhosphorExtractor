from .relex import Snowball
from .model.model import Ep
from . import Document
from .multi_rel_handle import MultiHandle
from .recorder import phos_recorder
from collections import Counter
import json
import os
import re
from .dictionary import Dictionary
class Sentence2dic():
    def __init__(self, text):
        self.text = text

    def to_dict(self):
        return {
            'sentence:': self.text}
    def __str__(self):
        return self.text
class EmissionPeakDB():
    def __init__(self,save_root,filename,file_list):
        self.dic = None
        self.filename = filename
        self.count = 0
        self.save_root = save_root
        self.total_records = []
        self.file_list = file_list
        self.dictionary = Dictionary()
        self.snowball_a = Snowball.load(r'.../emissions_concentration.pkl')
        self.snowball_a.save_dir = r'.../chemdataextractor/relex/data'
        self.snowball_a.save_file_name = 'test_a'
        self.snowball_b = Snowball.load(r'.../ep_only.pkl')
        self.snowball_b.save_dir = r'.../chemdataextractor/relex/data'
        self.snowball_b.save_file_name = 'test_b'
        
    def save_to_file(self):
        with open('{}/{}.json'.format(self.save_root,self.filename), 'a', encoding='utf-8') as json_file:
            json.dump(self.dic, json_file, ensure_ascii=False)
            json_file.write('\n')
        return 
    def save_sentence(self,s):
        ini = Sentence2dic(text=str(s))
        with open('{}/{}.json'.format(self.save_root,'sentence'), 'a', encoding='utf-8') as json_file:
            json.dump(ini.to_dict(), json_file, ensure_ascii=False)
            json_file.write('\n')
        return 
    def write_2_dic(self,subject,object,unit,doi,sentence):
        results_multisom = {
            'phosphor': subject,
            'emission_peak': object,
            'unit': unit,
            'doi': doi,
            'note': 'results_multi'
            }
        print(f'results_multisom: {results_multisom}')
        self.dic = results_multisom
        self.save_to_file()
        self.save_sentence(sentence)
        
    def write_2_dic_2(self,excite,subject,object,unit,doi,sentence):
        results_multisom = {
            'phosphor': subject,
            'emission_peak': object,
            "excitation peak":excite,
            'unit': unit,
            'doi': doi,
            'note': 'results_multi'
            }
        print(f'results_multisom: {results_multisom}')
        self.dic = results_multisom
        self.save_to_file()
        self.save_sentence(sentence)
    
    def compound_extra(self,pors):
        pors.add_models([Ep])
        list = pors.records.serialize()
        results_both = []
        results_phos = []
        for item in list:
            if 'Ep' in item.keys():
                phosphor = item['Ep'].get('phosphors', None)
                results_phos.append(phosphor)
                if 'phosphors' in item['Ep'].keys() and 'emission_peak' in item['Ep'].keys():
              
                    results_both.append(item)                  
            else:
                return None
            
    def combine_candi_pre(self,p):
        names = []
        phosphors = []
        p_cem = []
        most_common_items = []
        for s in p.sentences:
            s.models = [Ep]
            auto_records = s.records.serialize()
            for record in auto_records:
                if 'Compound' in record:
                    name = record['Compound'].get('names', [])
                    for n in name:
                        if 3<= len(str(n)) <5 and n.endswith('+'):
                            continue
                        if len(str(n)) >= 3:
                            names.append(n)
                if 'Ep' in record:
                    phos = record['Ep'].get('phosphors', [])
                    for n in phos:
                        if 3<= len(str(n)) <5 and n.endswith('+'):
                            continue
                        if len(str(n)) >= 3:
                            phosphors.append(n)                    
                   
                p_cem.extend(names)
                p_cem.extend(phosphors)  
        if p_cem:
            counter = Counter(p_cem)
            max_count = max(counter.values())
            most_common_items = [item for item, count in counter.items() if count == max_count]
             
        return most_common_items    
    def entity_2_text(self,sub,obj):
        
        sub_text = []
        obj_text = []
        for su in sub:
            sub_text.append(su.text)
        for ob in obj:
            obj_text.append(ob.text)            
        length_sub = len(sub_text)
        #length_prop = len(prop)
        length_obj = len(obj_text)            
        return length_sub,length_obj,sub_text,obj_text
    def s_o_m(self,s,sub,obj,prop,unit,doi,excitation):
        exci = excitation
        length_sub,length_obj,sub_text,obj_text = self.entity_2_text(sub,obj)
        print('in som sub_text,obj_text:',sub_text,obj_text)
        for q in range(0,length_sub):            
            subject = sub_text[q]
            object = obj_text[q]
            if exci:
                #print(sentence_tokens)
                self.write_2_dic_2(exci,subject,object,unit,doi,s)
            else:    
                #print(sentence_tokens)
                self.write_2_dic(subject,object,unit,doi,s)
        return subject,object
 
    def s_o_o(self,s,sub,obj,prop,unit,doi,excitation):
        length_sub,length_obj,sub_text,obj_text = self.entity_2_text(sub,obj)
        token_id = {}
        
        distance_os = []
        exci = excitation
        for subentity in sub:
            for objentity in obj:
                length_so = abs(subentity.start - objentity.start)
                distance_os.append(length_so)
        for g in range(0,length_obj):
            id_min = distance_os.index(min(distance_os))
            if id_min < length_obj:
                subject = sub_text[0]
                object = obj_text[id_min]
            else: 
                #s3 o2 dis6 ,chose last 2 min distance apare s and o 
                m,n = divmod(id_min,length_obj)
                object = obj_text[n]
                subject = sub_text[m]
            distance_os.pop(id_min)
            if exci:
                #print(sentence_tokens)
                self.write_2_dic_2(exci,subject,object,unit,doi,s)
            else:
                #print(sentence_tokens)    
                self.write_2_dic(subject,object,unit,doi,s)
        return
            
    def s_l_o(self,s,sub,obj,prop,unit,doi,excitation):
        token_list = s.raw_tokens
        exci = excitation
        add_dic = {}
        distance_po = []
        length_sub,length_obj,sub_text,obj_text = self.entity_2_text(sub,obj)      
        if length_sub == length_obj and length_sub == 1:
            subject = sub_text[0]
            object = obj_text[0]
            if exci:
                self.write_2_dic_2(exci,subject,object,unit,doi,s)
            else:    
                self.write_2_dic(subject,object,unit,doi,s)
                
        elif length_sub == length_obj and length_sub > 1:
            self.s_o_m(s.raw_tokens, sub, obj, prop,unit,doi,excitation)
             
        elif length_sub < length_obj and length_sub == 1:
            subject = sub_text[0]
            object = obj_text
            if exci:
                self.write_2_dic_2(exci,subject,object,unit,doi,s)
            else:    
                self.write_2_dic(subject,object,unit,doi,s)
               
        elif 1 < length_sub < length_obj and (length_obj-length_sub) == 1:
            distances = [abs(obj[i].start - obj[i-1].start) for i in range(1, len(obj))]
            min_distance_idx = distances.index(min(distances))
            if min(distances) < 4:
                obj_1 = obj[min_distance_idx]
                obj_2 = obj[min_distance_idx + 1]
                object1 = []
                if 'and' in token_list[obj_1.start:obj_2.end]:                   
                    object1.append(obj_1.text)
                    object1.append(obj_2.text)
                    #print('object1:',object1)
                    dd = {obj_1.text:object1}
                    object_new = [dd[i] if i in dd else i for i in obj_text] 
                    object_new.remove(obj_2.text)
                #slice = token_list[obj_1.start:obj_2.end]
                    #print('object1:',object1)
                    for n in range(0,length_sub):
                        subject = sub_text[n]
                        object = object_new[n]
                        if exci:
                            self.write_2_dic_2(exci,subject,object,unit,doi,s)
                        else:    
                            self.write_2_dic(subject,object,unit,doi,s)
                          
                        
            else:               
                for subentity in sub:
                    distance_os = []
                    for objentity in obj:
                        length_so = abs(subentity.start - objentity.start)
                        distance_os.append(length_so)
                    id_min = distance_os.index(min(distance_os))
                    object = obj_text[id_min]
                    obj_text.pop(id_min)
                    obj.pop(id_min)
                    subject = subentity.text
                    if exci:
                        self.write_2_dic_2(exci,subject,object,unit,doi,s)
                    else:    
                        self.write_2_dic(subject,object,unit,doi,s)
        return              
                                              

                    
                
    def extract_names_and_phosphors(self,most_common_items,obj_text,unit,doi,excitation,s):
        exci = excitation
        if exci:
            results_combine = {
                'phosphor': most_common_items,'emission_peak': obj_text,'excitation peak': exci,'unit': unit,'doi': doi,'note': 'results_combine'}
            self.dic = results_combine
            self.save_to_file()
            self.save_sentence(s)
            print(f'results_combine: {results_combine}')
        else:
            results_combine = {
                'phosphor': most_common_items,'emission_peak': obj_text,'unit': unit,'doi': doi,'note': 'results_combine'}
            self.dic = results_combine
            self.save_to_file()
            self.save_sentence(s)
            print(f'results_combine: {results_combine}')          
        return 
    def process_paragraph(self, s, sub_text,obj_text,unit,doi,excitation):
        a = self.snowball_a       
        b = self.snowball_b
        exci = excitation       
        candidate_relationship = a.extract(s)
        lacked_relationship = b.extract(s)
        if candidate_relationship is not None:
            Recorder = phos_recorder(candidate_relationship=candidate_relationship, lacked_relationship=lacked_relationship, total_records=self.total_records, filename=self.filename, save_root=self.save_root)
            Output = Recorder.recorder()
        else:
            if exci: 
                results_auto = {
                    'phosphor': sub_text,'emission_peak': obj_text,'excitation peak':exci,'unit': unit,'doi': doi,'note': 'results_auto'}
                self.dic = results_auto
                self.save_to_file()
                self.save_sentence(s)
                #print(f'sentence: {s}')
                print(f'results_auto: {results_auto}')
            else:
                results_auto = {
                    'phosphor': sub_text,'emission_peak': obj_text,'unit': unit,'doi': doi,'note': 'results_auto'}
                self.dic = results_auto
                self.save_to_file()
                self.save_sentence(s)
                #print(f'sentence: {s}')
                print(f'results_auto: {results_auto}')           
                            
    def classify(self, p,file_name):
        most_common_items = self.combine_candi_pre(p)
        #print('most_common_items:',most_common_items)
        for s in p.sentences:
            s.models = [Ep]
            auto_records = s.records.serialize()
            for record in auto_records:
                if 'Ep' in record:
                    ep_data = record['Ep']
                    phosphors = ep_data.get('phosphors', [])
                    emission_peak = ep_data.get('emission_peak', [])
                    unit = ep_data.get('unit', None)
                    doi = file_name.replace('.txt','').replace('https%3A%2F%2Fapi.elsevier.com%2Fcontent%2Farticle%2Fdoi%2F', '').replace('.json', '').replace('.pdf', '')

                    handle = MultiHandle(s)
                    sub = handle.sub_list
                    obj = handle.obj_list
                    prop = handle.prop_list
                    excitation = handle.exci
                    length_sub,length_obj,sub_text,obj_text = self.entity_2_text(sub,obj)

                    if phosphors and emission_peak:

                        if sub_text:
                            if handle.classification == 'sub_obj':
                                 #print('Now enter in sub_obj')
                                self.process_paragraph(s, sub_text,obj_text,unit,doi,excitation)
                            if handle.classification == 'sub_obj_multi':
                                 #print('Now enter in som')                           
                                self.s_o_m(s.raw_tokens,sub,obj,prop,unit,doi,excitation)                               
                                   
                            if handle.classification == 'sub_over_obj':
                                 #print('Now enter in soo')
                                self.s_o_o(s.raw_tokens,sub,obj,prop,unit,doi,excitation)
                                    
                            if handle.classification == 'sub_less_obj':
                                self.s_l_o(s, sub, obj, prop,unit,doi,excitation)
                                    
                        else:
                            # print('Now need combine1')
                            if most_common_items:
                                self.extract_names_and_phosphors(most_common_items,obj_text,unit,doi,excitation,s)        
                    elif not phosphors and emission_peak:
                        # print('Now need combine2')
                        print(f'sentence: {s}')
                        if most_common_items:
                            self.extract_names_and_phosphors(most_common_items,emission_peak,unit,doi,excitation,s)    
                               

    def BatchExtract(self):
        corpus_list = os.listdir(self.file_list)
        for i, file_name in enumerate(corpus_list):
            print(f'\n{i + 1}/{len(corpus_list)}: {file_name}')
            file_path = os.path.join(self.file_list, file_name)
            with open(file_path, 'rb') as f:
                d = Document.from_file(f)
                for p in d.paragraphs:
                    self.classify(p, file_name)

