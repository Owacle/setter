# Functions for saving and loading multiple types of objects in maya
# Does some expanding of collections that maya does of the form [a:b] where a....b represents a range

import maya.cmds as cmds
import os
import xml.etree.ElementTree as ET

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
    
    def get_existing_items(self):
        '''
        first check that the items exist before you do the return
        I think this could be a pre-processing step
        '''
        # test_list = ['head.top', 'hand|something', 'another']
        # return_list = [x for x in test_list if cmds.objExists(x)]
        return_list = [x for x in self._items if cmds.objExists(x)]

        return return_list

    def add_items(self, items):
        for each in items:
            self.add_item(each)
    
    def add_item(self, item):
        self._items.append(item)
        
    def clear_items(self):
        self._items = []
        
    def set_name(self, name):
        self._name=name
        
    def print_set(self):
        print('%s'%self._name)
        for item in self._items:
            print('  %s'%item)

class SelectionSetList():
    '''
    this is a collection of SelectionSet() objects
    '''
    
    def __init__(self):
        self._collections=[]
            #convenience item to potentially speed things up later for large number of sets
        self._num_lists = 0
        self._tree = ''
        
    def load_from_xml(self, filename):
        '''
        loads a file from disk into a list of SelectionSet objects
        also builds the xml tree 
        '''

        if len(filename) == 0:
            print('no file specified')
            return
        self._tree = ET.parse(filename)
        root = self._tree.getroot()
        for each in root.getchildren():
            self._num_lists += 1
            new_set = SelectionSet()
            #each is a whole set
            new_set.set_name(each.get('name'))
            for item in each.getchildren():
                new_set.add_item(item.text)
            self._collections.append(new_set)
    
    def write_to_xml(self, filename):
        '''
        writes the current xml tree out to disk
        '''
        if(len(filename)==0):
            print 'no file specified'
            return
        self._tree.write(filename)
        #also writes a semi pretty one
        with open(filename[:-4]+'_pretty.xml', 'w') as openfile:
            openfile.write(self.prettify(self._tree.getroot()))
        openfile.close()
    
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
     
    def add_set(self, name, list_items):
        '''
        used to add a named set to the list of sets
        also adds the same to the xml tree
        '''
        # print('adding a list called %s'%name)
        # print(list_items)
        
        # make a new set object and put the items into it
        new_set = SelectionSet()
        new_set.set_name(name)
        new_set.add_items(list_items)
        
        # add the set to the list of sets
        self._collections.append(new_set)
        
        # update the xml tree with the same thing, ready for writing out
        root = self._tree.getroot()
        new_el = ET.Element('set')
        new_el.set('name',name)
        for each in list_items:
            new_sub = ET.Element('item')
            new_sub.text = each
            new_el.append(new_sub)
        
        root.append(new_el)
       
    def rebuild_tree(self):
        '''
        clear the tree and build from the collection
        '''
        root = ET.Element('sets')
        for each in self._collections:
            new_el = ET.SubElement(root, 'set')
            new_el.set('name',each.get_name())
            for one_item in each.get_items():
                new_sub = ET.Element('item')
                new_sub.text = one_item
                new_el.append(new_sub)
        self._tree = ET.ElementTree(root)
        # new_tree = 
        # temp_pwd = os.path.dirname(__file__)
        # new_tree.write(temp_pwd+'/output_test_mega.xml')
        

    def get_set_by_name(self, name):
        set_names = [x.get_name() for x in self._collections] 
        all_matching = [x for x in set_names if x == name]
        return all_matching
        
    def print_all(self):
        for one_set in self._collections:
            one_set.print_set()


    def expand_maya_set(self, what):
        '''
        expand out the maya notation of [a:b] for a range into individual items
        RETURN: a list of each
        '''
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

    # this wont work because its not a dictionary anymore

    # def replace_collection(self, which_collection, what):
    #     new_what = self.expand_maya_set(what)
    #     self._collections[which_collection] = new_what


    def replace_set(self, index, what):
        '''
        Accepts a SelectionSet object and replaces the index specified 
        '''
        self._collections[index] = what

    def replace_set_from_list(self, index, name, item_list):
        '''
        takes a list of items and expands it then makes a SelectionSet object to add to the collection
        '''
        expanded_list = self.expand_maya_set(item_list)
        new_set = SelectionSet()
        new_set.set_name(name)
        new_set.add_items(expanded_list)
        self.replace_set(index, new_set)
        self.rebuild_tree()

    def add_to_collection(self, which_collection, what):
        '''
        think it should try and work with lists and a SelectionSet object
        '''
        print 'add to collection: '+what
        # new_what = self.expand_maya_set(what)
        # if self._collections[which_collection] == ['empty']:
        #     self._collections[which_collection] = new_what
        # else:
        #     self._collections[which_collection] += new_what

    def remove_from_collection(self, which_collection, what):
        '''
        think it should try and work with lists and a SelectionSet object
        '''
        print 'remove from collection: '+what

        # orig = self._collections[which_collection]
        # new_what = self.expand_maya_set(what)
        # self._collections[which_collection] = [x for x in orig if x not in new_what]

    def get_blind_collection(self, which_collection):
        ''' not sure I remember what this is supposed to do'''
        print 'not sure - pass'
        # full_name_collection = self._collections[which_collection]
        # blind_collection = []
        # for each in full_name_collection:
        #     blind_collection.append(each.partition('.')[2])
        # return blind_collection

    def get_collection(self, index):
        '''
        think it should try and work with lists and a SelectionSet object
        Returns a SelectionSet()
        '''
        print 'get collection: '+str(index)
        if len(self._collections) > index:
            return self._collections[index]
        # if self._collections[which_collection] == ['empty']:
        #     return None
        # else:
        #     return self._collections[which_collection]

    def get_all(self):
        return self._collections

## end of class  ---- Collection_Saver()
            
        
# test_set_list = SelectionSetList()
# path_full = os.path.dirname(__file__)
# test_set_list.load_from_xml(path_full+'/sets.xml')
# test_set_list.print_all()

# test_set_list.add_set(name='bobby', list_items=['head','tail','another'])
# test_set_list.print_all()
# test_set_list.write_to_xml(path_full+'/sets_out.xml')

# btest_set_list = SelectionSetList()
# btest_set_list.load_from_xml(path_full+'/sets_out.xml')
# btest_set_list.print_all()
# btest_set_list.add_set(name='one more', list_items=['foot', 'toe'])
# btest_set_list.write_to_xml(path_full+'/sets_out.xml')


class Collection_Saver():
    '''A class for doing the majority of the handling of the selection lists'''
    
    def __init__(self):
        self._all_sel_sets = SelectionSetList()
        self._pwd = os.path.dirname(__file__)
        # self.write_xml_buttons()

    def load_collections_xml(self, filename):
        '''
        the xml should be in the user directory
        '''
        # returns a list of SelectionSet objects
        self._all_sel_sets.load_from_xml(self._pwd+'/'+filename)


        # loaded_collections = {'A':['empty'], 'B':['empty'], 'C':['empty'], 'D':['empty'], 'E':['empty']}
        # # first go and see if there is one
        # # if there isn't, make one
        #     # return an empty set of collections
        
        # return loaded_collections
        # if there is, load it
            # return the loaded collections
 
    def write_collections_xml(self, filename):
        '''
        write the same thing but this time in XML format somehow
        '''
        self._all_sel_sets.write_to_xml(self._pwd+'/'+filename)

        # alltabs = []
        # window_element = ET.Element('sets')
        # for set_group in self._collections:
        #     print set_group
        #     tab_element = ET.SubElement(window_element, 
        #                                     tag='selection_set', 
        #                                     title=str(set_group))
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
        # tree = ET.ElementTree(window_element)
        # # tree.write(self._pwd+'/output.xml')
        # file_name = self._pwd+'/outputnice.xml'
        # with open(file_name, 'w') as openfile:
        #     openfile.write(self.prettify(window_element))
        # openfile.close()


    # def show_all_collections(saver_obj):
    #     def show_all_sub(*args):
    #         for line in saver_obj.get_all():
    #             print line
    #     return show_all_sub

    def output_to_xml(self, filename):
        def output_sub(*args):
            '''
            first rebuilds the internal tree to match the list
            Then writes to the specified file
            '''
            self._all_sel_sets.rebuild_tree()
            self._all_sel_sets.write_to_xml(self._pwd+'/'+filename)
        return output_sub

    def load_save_set(self, index, operation='save',label='no_label'):
        def save_sub(*args):
            '''
            general purpose button press function to load/save/edit the collections

            '''
            coll = self._all_sel_sets.get_collection(index)
            if operation == 'load' and (coll != None):
                items = coll.get_existing_items()
                cmds.select(items)
            elif operation == 'deselect' and (coll != None):
                cmds.select(coll, deselect=True)
            else:
                seled = cmds.ls(sl=True)
                if not seled:
                    print 'nothing selected - think about clearing'
                elif operation == 'save':
                    #self._all_sel_sets.replace_collection(index,seled)
                    self._all_sel_sets.replace_set_from_list(index, label, seled)
                    self.write_collections_xml('sets_out_mega.xml')
                    print 'text_label is: '+label
                    if len(label)>0:
                        cmds.text([label], edit=True, backgroundColor=[1,1,1])
                elif operation == 'add':
                    self._all_sel_sets.add_to_collection(index, seled)
                elif operation == 'remove':
                    self._all_sel_sets.remove_from_collection(index, seled)
                else:
                    print 'unknown operation'
        return save_sub

    def make_set_buttons(self, set_name, index, col=[0.8,0.8,0.8]):

        saver = self._all_sel_sets
        set_name_bkt = '['+set_name+']'

        dim_col = [(x*0.2)+0.2 for x in col]
        text_label = cmds.text(label='*',
                               backgroundColor=[0.2,0.2,0.2])
        #cmds.text(label=set_name_bkt,
        #          backgroundColor=col)
        cmds.button( label=set_name_bkt, 
                     backgroundColor=col,
                     command=self.load_save_set(index=index,
                                           operation='load'))
        cmds.button( label='Save', 
                     backgroundColor=dim_col,
                     #enableBackground=False,
                     command=self.load_save_set(index=index,
                                           operation='save',
                                           label=text_label))
        cmds.button( label=' + ', 
                     backgroundColor=dim_col,
                     command=self.load_save_set(index=index,
                                           operation='add'))
        cmds.button( label=' - ', 
                     backgroundColor=dim_col,
                     command=self.load_save_set(index=index,
                                           operation='remove'))
        cmds.button( label='Select', 
                     backgroundColor=dim_col,
                     command=self.load_save_set(index=index,
                                           operation='load'))
        cmds.button( label='Deselect', 
                     backgroundColor=dim_col,
                     command=self.load_save_set(index=index,
                                           operation='deselect'))

    def show(self):
        if cmds.window("SelectionSets", exists=True):
            cmds.deleteUI("SelectionSets")

        saver = self._all_sel_sets
        mainwindow = cmds.window("SelectionSets", title="Selections", height=100)
        
        cmds.rowColumnLayout(numberOfColumns=7, columnWidth=[(1, 20), 
                                                             (2, 80), 
                                                             (3, 50),
                                                             (4, 30),
                                                             (5, 30),
                                                             (6, 60), 
                                                             (7, 60)])
        for i, item in enumerate(self._all_sel_sets.get_all()):
            self.make_set_buttons(set_name=item.get_name(), index=i, col=[0.8,0.2,0.2])
        cmds.button( label='.')
        cmds.button( label='save to xml', 
                     command=self.output_to_xml('sets_out_mega.xml'))

        cmds.showWindow(mainwindow)

my_saver = Collection_Saver()
my_saver.load_collections_xml('sets_out_mega.xml')
my_saver.show()