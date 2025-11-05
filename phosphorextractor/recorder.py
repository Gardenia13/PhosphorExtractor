from chemdataextractor.relex import Snowball
from chemdataextractor.model.model import Phosphor,Compound
from chemdataextractor import Document
import json
import os


class phos_recorder:
    def __init__(self, candidate_relationship,lacked_relationship,total_records,filename,save_root):
        self.candidate_relationship = candidate_relationship
        self.lacked_relationship = lacked_relationship
        self.total_records = total_records
        self.dic = None
        self.filename = filename
        self.count = 0
        self.save_root = save_root

    def save_to_file(self):
        with open('{}/{}.json'.format(self.save_root,self.filename), 'a', encoding='utf-8') as json_file:
            json.dump(self.dic, json_file, ensure_ascii=False)
            json_file.write('\n')

        return    

    def recorder(self):
        if isinstance(self.candidate_relationship, (list, tuple)):
            filtered_entities = []
            phosphors = []
            peaks = []
            units = []
            for h in self.candidate_relationship:                   
                if isinstance(h.entities, (list, tuple)):
                    for j in h.entities:
                        if j.tag == 'phosphor':
                            phosphors.append(j)
                        elif j.tag == 'peaks':
                            peaks.append(j)
                        elif j.tag == 'units':
                            units.append(j)
                else:
                        print("Non-iterable entity:", h.entities)
                        # 如果不是可迭代的，这里可以考虑将其转换为列表
                        h.entities = [h.entities]
                        print("Entities:", h.entities)
                        for j in h.entities:
                            if j.tag == 'phosphor':
                                phosphors.append(j)
                            elif j.tag == 'peaks':
                                peaks.append(j)
                            elif j.tag == 'units':
                                units.append(j)            
            for phosphor in phosphors:    
                for peak in peaks:
                    for unit in units:
                        entity_dict = {
                                "phosphor": phosphor.text,
                                "emission peaks": peak.text +' '+ unit.text,
                            }
                        filtered_entities.append(entity_dict)
                        self.total_records.append(entity_dict)
                        record = {"Number":len(self.total_records),
                                    "phosphor":phosphor.text,
                                    "emission peaks":peak.text +' '+ unit.text,
                "Confidence":self.candidate_relationship[0].confidence,
                "note":str('results_snowball')}
                        self.dic = record
                        self.save_to_file()
                        
            print('\n',"Found : ", filtered_entities,'\n',"Confidence: ",self.candidate_relationship[0].confidence,'\n')   
        else:
            raise ValueError("candidate_relationship should be a list or tuple but got {}".format(type(self.candidate_relationship)))
        return 
    
    def recorder_incomplete(self,temp):
            if isinstance(self.lacked_relationship, (list, tuple)):
                filtered_entities = []

                peaks = []
                units = []
                for h in self.lacked_relationship:
                    
                    if isinstance(h.entities, (list, tuple)):
                        for j in h.entities:
                            #if j.tag in retain_labels:
                            if j.tag == 'peaks':
                                peaks.append(j)
                            elif j.tag == 'units':
                                units.append(j)
                    else:
                            print("Non-iterable entity:", h.entities)
                            # 如果不是可迭代的，这里可以考虑将其转换为列表
                            h.entities = [h.entities]
                            print("Entities:", h.entities)
                            for j in h.entities:
                                if j.tag == 'peaks':
                                    peaks.append(j)
                                elif j.tag == 'units':
                                    units.append(j) 
                for peak in peaks:
                    for unit in units:
                        entity_dict = {
                                            "emission peaks": peak.text +' '+ unit.text,
                                        }
                        filtered_entities.append(entity_dict)
                        self.total_records.append(entity_dict)
                        record = {"Number":len(self.total_records),
                                    "phosphor":temp,
                                    "emission peaks":peak.text +' '+ unit.text,
                                    "Confidence":self.lacked_relationship[0].confidence}
                        self.dic = record
                        self.save_to_file()
                        
                        print('\n',"Found : ", filtered_entities,'\n',"Confidence: ",self.lacked_relationship[0].confidence,'\n')   
                        
                print("Lacked relationship:", self.lacked_relationship)