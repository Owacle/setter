# Functions for saving and loading multiple types of objects in maya
# Does some expanding of collections that maya does of the form [a:b] where a....b represents a range

#import maya.cmds as cmds
import xml.etree.ElementTree as ET
import os

class SelectionSet():
    '''
    this is a single set for selection
    has a name
    has a list of items
    '''
    def __init__(self):
        self._name='unnamed'
        self._items=[]
        
    def get_name(self):
        return self._name
        
    def get_items(self):
        return self._items
    
    def add_items(self, items):
        self._items.append(items)
    
    def add_item(self, item):
        self._items.append(item)
        
    def clear_items(self):
        self._items = []
        
    def set_name(self, name):
        self._name=name
        
    def print_set(self):
        print('%s'%self._name)
        for item in self._items:
            print '   '+item
        print (' ')*10

class SelectionSetList():
    '''
    this is a collection of SelectionSet() objects
    '''
    
    def __init__(self, filename=''):
        self._all_sel_sets=[]
            #convenience item to potentially speed things up later for large number of sets
        self._num_lists = 0
        if len(filename)>0:
            self.load_from_xml(filename)
        
    def load_from_xml(self, filename):
        tree = ET.parse(filename)
        root = tree.getroot()
        for each in root.getchildren():
            new_set = SelectionSet()
            #each is a whole set
            new_set.set_name(each.get('name'))
            for item in each.getchildren():
                new_set.add_item(item.text)
            self._all_sel_sets.append(new_set)
    
    def print_all(self):
        for one_set in self._all_sel_sets:
            one_set.print_set()
            
        
test_set_list = SelectionSetList()
test_set_list.load_from_xml('sets.xml')
#test_set_list.print_all()


class Collection_Saver():
    '''A class for doing the majority of the handling of the selection lists'''
    
    def __init__(self):
        self._collections = self.load_from_xml()
        self._pwd = os.path.dirname(__file__)
        self.write_xml_buttons()

    def load_from_xml(self):
        '''
        the xml should be in the user directory
        '''
        # with open(file_name, 'r') as openfile:
        #     self._all_lines = openfile.readlines()
        # openfile.close()

        loaded_collections = {'A':['empty'], 'B':['empty'], 'C':['empty'], 'D':['empty'], 'E':['empty']}
        # first go and see if there is one
        # if there isn't, make one
            # return an empty set of collections
        
        return loaded_collections
        # if there is, load it
            # return the loaded collections

    def prettify(self, elem):
        """Return a pretty-printed XML string for the Element.
        """
        from xml.dom import minidom
        try:
            rough_string = ET.tostring(elem, 'utf-8')
        except Exception, e:
            raise e
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="\t")
 
    def write_xml_buttons(self):
        '''
        write the same thing but this time in XML format somehow
        '''
        alltabs = []
        window_element = ET.Element('sets')
        for set_group in self._collections:
            print set_group
            tab_element = ET.SubElement(window_element, 
                                            tag='selection_set', 
                                            title=str(set_group))
            # for item in set_group[key]:
            #     print item
            # for button in tab.all_buttons():
            #     button_element = ET.SubElement(tab_element, 
            #                       tag='button', 
            #                       label=button.get_name(), 
            #                       left=str(button.get_left()),
            #                       top=str(button.get_top()),
            #                       height=str(button.get_height()),
            #                       width=str(button.get_width()),
            #                       bgcol=button.get_bgcol_str(),
            #                       command=str(button.get_command()))
            #     if button.get_command() == 'select':
            #         all_items = ''
            #         for item in button.get_items():
            #             all_items += str(item) + '\n\t\t\t\t'
            #         item_element = ET.SubElement(button_element, tag='items')
            #         item_element.text = all_items[:-5] # -5 to strip the new line and last set of tabs
            #     else:   
            #         for item in button.get_items():
            #             min_max = button.get_min_max(item)
            #             clean_item = button.get_item_only(item)
            #             #we still want to put in the min and max for relevant items
            #             if min_max:
            #                 item_element = ET.SubElement(button_element, 
            #                                              tag='item', 
                                                           
            #                                              min=min_max[0], 
            #                                              max=min_max[1])
            #                 item_element.text = clean_item
            #             else:
            #                 item_element = ET.SubElement(button_element, 
            #                                              tag='item', 
            #                                              value='coming_soon')
            #                 item_element.text = clean_item
        tree = ET.ElementTree(window_element)
        # tree.write(self._pwd+'/output.xml')
        file_name = self._pwd+'/outputnice.xml'
        with open(file_name, 'w') as openfile:
            openfile.write(self.prettify(window_element))
        openfile.close()

    def expand_maya_set(self, what):
        '''expand out the maya notation of [a:b] for a range into individual items'''
        expanded_what = []
        for each in what:
            if ':' in each:
                first_bracket = each.find('[')+1
                colon_index = each.find(':')
                starter = int(each[first_bracket:colon_index])
                ender = int(each[colon_index+1:-1])
                new_range = 'this:' + str(range(starter, ender+1))
                new_each = [each[:first_bracket] + str(x) + ']' for x in range(starter, ender+1)]
                #print each
                #print new_each
                expanded_what += new_each
                #print new_range
            else:
                expanded_what.append(each)
        return expanded_what

    def replace_collection(self, which_collection, what):
        new_what = self.expand_maya_set(what)
        self._collections[which_collection] = new_what

    def add_to_collection(self, which_collection, what):
        new_what = self.expand_maya_set(what)
        if self._collections[which_collection] == ['empty']:
            self._collections[which_collection] = new_what
        else:
            self._collections[which_collection] += new_what

    def remove_from_collection(self, which_collection, what):
        orig = self._collections[which_collection]
        new_what = self.expand_maya_set(what)
        self._collections[which_collection] = [x for x in orig if x not in new_what]


    def get_blind_collection(self, which_collection):
        ''' not sure I remember what this is supposed to do'''
        full_name_collection = self._collections[which_collection]
        blind_collection = []
        for each in full_name_collection:
            blind_collection.append(each.partition('.')[2])
        return blind_collection

    def get_collection(self, which_collection):
        if self._collections[which_collection] == ['empty']:
            return None
        else:
            return self._collections[which_collection]

    def get_all(self):
        return self._collections

## end of class  ---- Collection_Saver()

def show_all_collections(saver_obj):
    def show_all_sub(*args):
        for line in saver_obj.get_all():
            print line
    return show_all_sub

def load_save_set(saver_obj, which_set, operation='save',label=''):
    def save_sub(*args):
        '''general purpose button press function to load/save/edit the collections'''
        coll = saver_obj.get_collection(which_set)
        if operation == 'load' and (coll != None):
            cmds.select(coll)
            # else:
            #     print('Nothing in set ', which_set)
        elif operation == 'deselect' and (coll != None):
            cmds.select(coll, deselect=True)
        else:
            seled = cmds.ls(sl=True)
            if not seled:
                print 'nothing selected - think about clearing'
            elif operation == 'save':
                saver_obj.replace_collection(which_set,seled)
                print 'text_label is: '+label
                if len(label)>0:
                    cmds.text([label], edit=True, backgroundColor=[1,1,1])
            elif operation == 'add':
                saver_obj.add_to_collection(which_set, seled)
            elif operation == 'remove':
                saver_obj.remove_from_collection(which_set, seled)
            else:
                print 'unknown operation'
    return save_sub

'''
def select_similar(saver_obj):
    def select_similar_sub(*args):
        seled = cmds.ls(sl=True)
        similar_selection = []
        similar_elements = saver_obj.get_blind_collection('e')
        for obj in seled:
            sim_list = [obj+'.'+x for x in similar_elements]
            similar_selection += sim_list
        cmds.select(similar_selection)
    return select_similar_sub
'''

def make_set_buttons(set_name, collection_saver, col=[0.8,0.8,0.8]):

    saver = collection_saver
    set_name_bkt = '['+set_name+']'

    dim_col = [(x*0.2)+0.2 for x in col]
    text_label = cmds.text(label='*',
                           backgroundColor=[0.2,0.2,0.2])
    #cmds.text(label=set_name_bkt,
    #          backgroundColor=col)
    cmds.button( label=set_name_bkt, 
                 backgroundColor=col,
                 command=load_save_set(saver,
                                       which_set=set_name,
                                       operation='load'))
    cmds.button( label='Save', 
                 backgroundColor=dim_col,
                 #enableBackground=False,
                 command=load_save_set(saver,
                                       which_set=set_name,
                                       operation='save',
                                       label=text_label))
    cmds.button( label=' + ', 
                 backgroundColor=dim_col,
                 command=load_save_set(saver,
                                       which_set=set_name,
                                       operation='add'))
    cmds.button( label=' - ', 
                 backgroundColor=dim_col,
                 command=load_save_set(saver,
                                       which_set=set_name,
                                       operation='remove'))
    cmds.button( label='Select', 
                 backgroundColor=dim_col,
                 command=load_save_set(saver,
                                       which_set=set_name,
                                       operation='load'))
    cmds.button( label='Deselect', 
                 backgroundColor=dim_col,
                 command=load_save_set(saver,
                                       which_set=set_name,
                                       operation='deselect'))

def show():
    if cmds.window("SelectionSets", exists=True):
        cmds.deleteUI("SelectionSets")

    saver = Collection_Saver()
    mainwindow = cmds.window("SelectionSets", title="Selections", height=100)
    cmds.rowColumnLayout(numberOfColumns=7, columnWidth=[(1, 20), 
                                                         (2, 50), 
                                                         (3, 50),
                                                         (4, 30),
                                                         (5, 30),
                                                         (6, 60), 
                                                         (7, 60)])
    
    make_set_buttons(set_name='A', collection_saver=saver, col=[0.8,0.2,0.2])
    make_set_buttons(set_name='B', collection_saver=saver, col=[0.2,0.8,0.1])
    make_set_buttons(set_name='C', collection_saver=saver, col=[0.2,0.4,0.9])
    make_set_buttons(set_name='D', collection_saver=saver, col=[0.9,0.8,0.2])
    make_set_buttons(set_name='E', collection_saver=saver, col=[0.6,0.2,0.7])

    cmds.showWindow(mainwindow)

#show()