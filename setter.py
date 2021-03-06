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
        
    def size(self):
        return self._num_lists

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
                #print item.text.strip(),
                new_set.add_item(item.text.strip())
            self._collections.append(new_set)
    
    def write_to_xml(self, filename):
        '''
        writes the current xml tree out to disk
        '''
        if(len(filename)==0):
            print 'no file specified'
            return
        with open(filename, 'w') as openfile:
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
        
        # make a new set object and put the items into it
        new_set = SelectionSet()
        new_set.set_name(name)
        new_set.add_items(list_items)
        
        # add the set to the list of sets
        self._collections.append(new_set)

        self._num_lists += 1
        
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

    def remove_from_collection(self, which_collection, what):
        '''
        think it should try and work with lists and a SelectionSet object
        '''
        print 'remove from collection: '+what

    def remove_collection(self, index):
        self._collections.pop(index)
        self._num_lists -= 1


    def get_collection(self, index):
        '''
        think it should try and work with lists and a SelectionSet object
        Returns a SelectionSet()
        '''
        if len(self._collections) > index:
            return self._collections[index]

    def get_all(self):
        return self._collections

    def rename_set(self, index, name):
        self._collections[index].set_name(name)



## end of class  ---- Collection_Saver()

class Collection_Saver():
    '''A class for doing the majority of the handling of the selection lists'''
    
    def __init__(self):
        self._all_sel_sets = SelectionSetList()
        self._pwd = os.path.dirname(__file__)

    def load_collections_xml(self, filename):
        '''
        the xml should be in the user directory
        '''
        # returns a list of SelectionSet objects
        self._all_sel_sets.load_from_xml(self._pwd+'/'+filename)

    def write_collections_xml(self, filename):
        '''
        write the same thing but this time in XML format somehow
        '''
        self._all_sel_sets.write_to_xml(self._pwd+'/'+filename)

    def modifier_pressed(self):
        '''
        return the string associated with the currently held modifier key
        '''
        mods = cmds.getModifiers()
        return_list = []
        if (mods & 1) > 0: return_list.append('SHIFT')
        if (mods & 2) > 0: return_list.append('CAPSLOCK')
        if (mods & 4) > 0: return_list.append('CONTROL')
        if (mods & 8) > 0: return_list.append('ALT')

        return return_list

    def output_to_xml(self, filename):
        def output_sub(*args):
            '''
            first rebuilds the internal tree to match the list
            Then writes to the specified file
            '''
            self._all_sel_sets.rebuild_tree()
            self._all_sel_sets.write_to_xml(self._pwd+'/'+filename)
        return output_sub


    def select_with_mods(self, items):
        mods = self.modifier_pressed()
        if 'SHIFT' in mods:
            if 'CONTROL' in mods:
                #both - so deselect
                cmds.select(items, deselect=True)
            else:
                cmds.select(items, add=True)
        elif 'CONTROL' in mods:
            cmds.select(items, tgl=True)
        else:
            cmds.select(items)

    def load_save_set(self, index, operation='save',label='no_label'):
        def save_sub(*args):
            '''
            general purpose button press function to load/save/edit the collections
            '''
            coll = self._all_sel_sets.get_collection(index)
            if operation == 'load' and (coll != None):
                items = coll.get_existing_items()
                
                try:
                    self.select_with_mods(items)
                except Exception, e:
                    print 'None of the [%i] items are in the scene'%len(coll.get_items())#raise e
                    
            elif operation == 'deselect' and (coll != None):
                cmds.select(coll, deselect=True)
            else:
                seled = cmds.ls(sl=True)
                if not seled:
                    print 'nothing selected - think about clearing'
                elif operation == 'save':
                    self._all_sel_sets.replace_set_from_list(index, label, seled)
                    self.write_collections_xml('sets_out_mega.xml')
                    print 'text_label is: '+label
                elif operation == 'add':
                    self._all_sel_sets.add_to_collection(index, seled)
                elif operation == 'remove':
                    self._all_sel_sets.remove_from_collection(index, seled)
                else:
                    print 'unknown operation'
        return save_sub

    def rename(self, index):
        def rename_sub(*args):
            ''' rename the current index'''
            result = cmds.promptDialog(title='Rename Object',
                                        message='Enter Name:',
                                        button=['OK', 'Cancel'],
                                        defaultButton='OK',
                                        cancelButton='Cancel',
                                        dismissString='Cancel')
            if result == 'OK':
                text = cmds.promptDialog(query=True, text=True)
                cmds.text( self.set_buttons[index], label=text, edit=True)
                self._all_sel_sets.rename_set(index, text)

        return rename_sub


    def delete(self, index):
        def delete_sub(*args):
            '''delete the item after confirming'''
            result = cmds.confirmDialog(title='DELETE this set ?',
                                        button=['YES', 'NO'],
                                        defaultButton='YES',
                                        cancelButton='NO',
                                        dismissString='NO')
            if result == 'OK':
                self._all_sel_sets.remove_collection(index)
                self.show()

        return delete_sub

    def make_set_buttons(self, set_name, index, col=[0.8,0.8,0.8]):
        '''makes a row of buttons for each set in the set of sets'''

        dim_col = [(x*0.2)+0.2 for x in col]
 
        text_label = cmds.text(label=set_name)


        main_set_button = cmds.button( label='sel', 
                     backgroundColor=col,
                     command=self.load_save_set(index=index,
                                           operation='load'))
        cmds.button( label='Save', 
                     backgroundColor=dim_col,
                     command=self.load_save_set(index=index,
                                           operation='save'))
        cmds.button( label=' + ', 
                     backgroundColor=dim_col,
                     command=self.load_save_set(index=index,
                                           operation='add'))
        cmds.button( label=' - ', 
                     backgroundColor=dim_col,
                     command=self.load_save_set(index=index,
                                           operation='remove'))
        cmds.button( label='ren', 
                     command=self.rename(index=index))

        cmds.button( label='del', 
                     command=self.delete(index=index))

        return text_label

    def add_row(self, which_rowlayout):
        def add_row_sub(*args):

            self._all_sel_sets.add_set('new_set', 'front')
            self.show()

        return add_row_sub

    def show(self):
        if cmds.window("SelectionSets", exists=True):
            cmds.deleteUI("SelectionSets")

        this_window_height = (self._all_sel_sets.size() * 24) + 40

        mainwindow = cmds.window("SelectionSets", title="Selections", height=this_window_height)

        self.set_buttons = []

        form_main = cmds.formLayout(numberOfDivisions=100)
        
        rows = cmds.rowColumnLayout(numberOfColumns=7, 
                                    columnWidth=[(2,30),(3, 50),(4, 30), (5, 30),(6, 30)],
                                    columnAlign=(1,'left'),
                                    columnAttach=(1,'both',10))

        # make a row for each set
        for i, item in enumerate(self._all_sel_sets.get_all()):
            self.set_buttons.append( self.make_set_buttons(set_name=item.get_name(), index=i, col=[0.8,0.2,0.2]) )
        
        cmds.formLayout(form_main,
                        edit=True,
                        attachForm=((rows, 'top', 5), (rows, 'right', 10)))

        
        cmds.setParent('..')
        cmds.setParent('..')

        # now make the buttons at the bottom for saving and adding rows
        extra_rows = cmds.rowColumnLayout(numberOfColumns=2)
        cmds.formLayout(form_main,
                        edit=True,
                        attachForm=((extra_rows, 'bottom', 5), (extra_rows, 'right', 10)))
        cmds.button( label='save to xml', 
                     command=self.output_to_xml('sets.xml'))
        cmds.button( label='add new set', 
                     command=self.add_row(rows))

        cmds.showWindow(mainwindow)

# END of collection saver class

my_saver = Collection_Saver()
my_saver.load_collections_xml('sets.xml')
my_saver.show()