#!/usr/bin/python

from os import path, isatty
import argparse
import sys
import subprocess
from datetime import datetime
import pickle
import getpass

class LabbError(Exception):
        '''Base class for labb exceptions.'''
        pass

class tag:
        '''Add string 'tags' to entries for later implementation of filtering/searching.'''
        def __init__(self,text):
                self.__dict__.update({k:v for k,v in locals().items() if k!='self'})

class table:
        '''Data type for a table. Not yet implemented.'''
        pass

class image:
        '''Data type for an image. Simply holds an external image file.'''
        def __init__(self,filename,text):
                self.__dict__.update({k:v for k,v in locals().items() if k!='self'})

class equation:
        '''Latex-formatted equation, saved as a string.'''
        def __init__(self,text):
                self.__dict__.update({k:v for k,v in locals().items() if k!='self'})

class citation:
        '''Citation, saved as a string.'''
        def __init__(self,text):
                self.__dict__.update({k:v for k,v in locals().items() if k!='self'})

class code:
        '''Data type for a code or script. Simply holds an external source file.'''
        def __init__(self,filename,text):
                self.__dict__.update({k:v for k,v in locals().items() if k!='self'})

class note:
        '''Note, saved as a string.'''
        def __init__(self,text):
                self.__dict__.update({k:v for k,v in locals().items() if k!='self'})

class entry:
        '''Entry objects are appended to the entry list in the book class. They are 'open' when they are first added to the list.
They contain a data list which can be appended until the entry is closed.'''
        def __init__(self):
                self.data = []
                self.timestamp = datetime.utcnow()
                self.tags = []

class book:
        '''A book requires an introduction from the user, as well as an author and name. A directory is created in .labb to store files associated with data.
It contains a list of entries, as well as methods to open a new entry, add data to a current entry, and close an entry.'''
        def __init__(self,name,introduction):
                self.__dict__.update({k:v for k,v in locals().items() if k!='self'})
                self.directory = '.labb/books/' + name
                self.entries = []
                self.is_open = False

        def open(self):
                '''Checks to see if there are no open entries. If that is the case, it appends a new entry to the list in the book.'''
                if len(self.entries) == 0:
                        new_entry = entry()
                        self.entries.append(new_entry)
                        self.is_open = True

                elif self.is_open:
                        raise LabbError('There is already an open entry.')

                else:
                        self.is_open = True
                        self.entries.append(entry())

        def add_entry(self,entry_data):
                '''Checks to see if there is a current entry. Takes a datum and adds it to the data list in the current entry.
If the data type has an associated file, it is copied into the book's directory in .labb.'''
                if self.is_open:
                        if hasattr(entry_data,'filename'):
                                subprocess.call(['cp',entry_data.filename,self.directory])
                                original_file = path.basename(entry_data.filename)
                                backup_file = '.labb/books/'+self.name+'/'+original_file
                                entry_data.filename = path.abspath(backup_file)
                        self.entries[-1].data.append(entry_data)
                else:
                        raise LabbError('This book does not have an open entry.')

        def add_tag(self,the_tag):
                if self.is_open:
                        self.entries[-1].tags.append(the_tag)
                else:
                        raise LabbError('This book does not have an open entry.')

        def close(self):
                '''Checks to see if there is a current entry, and closes it.'''
                if self.is_open:
                        self.is_open = False
                else:
                        raise LabbError('This book does not have an open entry.')

class labb:
        '''A labb consists of a dictionary of books -- it associates a book's name with the book object.
Has methods to create new books, and fetch existing books. labb.current stores the name of the book to which one can submit new entries.'''
        def __init__(self):
                self.books = {}
                self.author = raw_input('Type the author name: ')
                self.current = None

        def new_book(self,book_name,book_introduction):
                '''Creates a new book.'''
                self.books[book_name] = book(book_name,book_introduction)
                subprocess.call(['mkdir','.labb/'+book_name])

        def change_current(self,book_name):
                '''Checks to see if the current book (if it exists) has an open entry.
If not, it changes the current book to book_name.'''
                if self.current != None and self.books[self.current].is_open:
                        raise LabbError('There is an open entry in the current book. Close this entry before changing books.')
                else:
                    self.current = book_name

        def print_book(self,book_name):
                '''prints to the terminal the text content of a book. in the near future, want to add in search filters and limits on the number of entries displayed.'''

                if book_name not in self.books:
                        raise LabbError('Book not found.')

                the_book = self.books[book_name]

                print the_book.name
                print self.author+'\n'
                print the_book.introduction+'\n'

                for ent in the_book.entries:
                        print ent.timestamp.strftime('%a %d %b %Y %X')

                        for datum in ent.data:
                                if hasattr(datum,'filename'):
                                        print '<<'+datum.filename+'>>'
                                print datum.text+'\n'

                        print 'Tags:'
                        for tag in ent.tags:
                                print tag.text

        def export_book(self,book_name,format_type):
                '''Takes a book, iterates over the entries, and produces a .tex file.'''
                if book_name not in self.books:
                        raise LabbError('Book not found.')

                the_book = self.books[book_name]

                export_filename = the_book.name+'.'+format_type
                export_file = open(export_filename,'w')

                #retrieve the format

                format_dict = {}

                for doc in ['intro','entry','note','equation','citation','image','tags','outro']:
                    with open('.labb/'+format_type+'/'+doc) as f:
                        format_dict[doc] = f.read()

                export_file.write(format_dict['intro'] % {'name': the_book.name,'author': self.author,'intro': the_book.introduction})

		#now loop over entries and make sections for each.

		for ent in the_book.entries:
			export_file.write(format_dict['entry'] % {'timestamp': ent.timestamp.strftime('%a %d %b %Y %X')})

			for dat in ent.data:
                                export_file.write(format_dict[dat.__class__.__name__] % { k:getattr(dat,k) for k in dir(dat) if not k.startswith('__')})

                        tagstring = ', '.join([t.text for t in ent.tags])

                        export_file.write(format_dict['tags'] % {'tags': tagstring})

		export_file.write(format_dict['outro']) #close the document.
                export_file.close()

def get_from_editor(initial=''):
        '''Method that opens vim, and saves a dummy text file. The contents of the dummy file are returned as a string. This is used by data types that need string input.'''
        from tempfile import NamedTemporaryFile
        with NamedTemporaryFile(delete=False) as tf: #create a temp file
                tfName = tf.name
                tf.write(initial)

        if subprocess.call(['vim',tfName]) != 0: #did vim succesfully close?
                raise LabbError('VIM did not successfully close.')

        with open(tfName) as tf:
            result = tf.read()
        if result == None:
                raise LabbError('Text entry failed.')
        return result

def process_input(editor_initial=''):
        if not isatty(0):
                text = sys.stdin.read() 
        else:
                text = get_from_editor(initial=editor_initial)
        return text.strip()

def save_labb(the_labb):
        '''Pickles a labb.'''
        outfile = open('.labb/labb.p','wb')
        pickle.dump(the_labb,outfile)
        outfile.close()

def open_labb():
        '''Opens the pickled labb.'''
        if path.exists('.labb/labb.p'):
                infile = open('.labb/labb.p','rb')
                the_labb = pickle.load(infile)
                infile.close()
                return the_labb
        else:
                raise LabbError('You have not yet initialized labb.')

def init_cmd(setup_path):
        if path.exists('.labb/labb.p'):
                raise LabbError('Already initialized in current directory.')
        if len(setup_path)!=1:
                raise LabError('labb-init expects one argument.')
        else:
                username = getpass.getuser()
                subprocess.call(['mkdir','.labb'])
                subprocess.call(['mkdir','.labb/books'])
                for ft in ['tex','md']:
                        subprocess.call(['mkdir','.labb'+'/'+ft])
                        for fn in [
                                    'intro',
                                    'note',
                                    'citation',
                                    'image',
                                    'entry',
                                    'equation',
                                    'tags',
                                    'outro'
                                  ]:
                                subprocess.call(['cp',setup_path[0]+'/'+ft+'/'+fn,'.labb/'+ft+'/'])
                the_labb = labb()
                save_labb(the_labb)
                print 'Labb initialized'

def book_cmd(the_labb,args):
        if len(args) == 0:
                for a_book in iter(the_labb.books):
                        if the_labb.current == a_book:
                                if not the_labb.books[a_book].is_open:
                                        print a_book+' *'
                                else:
                                        print a_book+' *o'
                        else:
                                print a_book

        elif len(args) == 1:
                if args[0] not in the_labb.books:
                        book_introduction = process_input()
                        the_labb.new_book(args[0],book_introduction)
                        print 'New book '+args[0]+' created.'
                the_labb.change_current(args[0])
                print 'Current book changed to '+the_labb.current+'.'
                save_labb(the_labb)

        else:
                raise LabbError('Specify at most one book.')


def check_for_books(the_labb):
        if the_labb.current == None:
                raise LabbError('You have no books yet.')

def entry_cmd(the_labb):
        the_labb.books[the_labb.current].open()
        save_labb(the_labb)
        print 'New entry opened in '+the_labb.books[the_labb.current].name+'.'

def close_cmd(the_labb):
        the_labb.books[the_labb.current].close()
        save_labb(the_labb)

def add_cmd(the_labb,args):
        '''this switch statement checks to see what the data type we want to add, and adds it.'''
        if not the_labb.books[the_labb.current].is_open:
                raise LabbError('There is no open entry.')

        if args.datatype == 'note': 
                note_text = process_input()
                new_note = note(note_text)
                the_labb.books[the_labb.current].add_entry(new_note)
                
        elif args.datatype == 'equation':
                equation_text = process_input() 
                new_equation = equation(equation_text)
                the_labb.books[the_labb.current].add_entry(new_equation)
                
        elif args.datatype == 'citation':
                citation_text = process_input()
                new_citation = citation(citation_text)
                the_labb.books[the_labb.current].add_entry(new_citation)

        elif args.datatype == 'image':
                if args.filename == None:
                        raise LabbError('Supply the image filename.')

                if path.exists(args.filename) == False:
                        raise LabbError('File does not exist.')
                
                image_text = process_input()
                new_image = image(args.filename,image_text)
                the_labb.books[the_labb.current].add_entry(new_image)

        save_labb(the_labb)

def add_tag_cmd(the_labb,args):
        if not the_labb.books[the_labb.current].is_open:
                raise LabbError('There is no open entry.')

        new_tag = tag(args.text[0])
        the_labb.books[the_labb.current].add_tag(new_tag)
        save_labb(the_labb)

def export_cmd(the_labb,args):
        the_labb.export_book(args.book[0],args.format_type[0])
        print 'Book '+args.book[0]+' exported.'

def show_cmd(the_labb,args):
        the_labb.print_book(args.book[0])

if __name__ == '__main__':
        #when executed, labb.py is a command to manipulate a labb object, which is pickled in a hidden directory .labb
        mainparser = argparse.ArgumentParser(prog='labb',description='A simple command-line logbook.') #create the parser
        mainparser.add_argument('--version', action='version', version='Current version is 0.1.')
        mainparser.add_argument('cmd',choices=['init','book','show','entry','add','tag','close','export']) #the possible commands to perform
        mainparser.add_argument('extra',nargs='*') #some commands require extra arguments
        mainargs = mainparser.parse_args() #this line actuall parses argv and returns the data to args

        if mainargs.cmd == 'init': #let's initialize. labb takes no extra arguments.
                initparser = argparse.ArgumentParser(prog='labb-init',description='Initialize labb in the current folder.')
                initparser.add_argument('setup_dir',nargs='*')
                initargs = initparser.parse_args(mainargs.extra)
                try:
                        init_cmd(initargs.setup_dir)
                except LabbError as err:
                        print err.message
                        sys.exit(1)
                sys.exit(0)

        try: #any further arguments require the actual labbook data.
                the_labb = open_labb()
        except LabbError as err:
                print err.message
                sys.exit(1)

        if mainargs.cmd == 'book': #with no additional arguments, this command displays all books, and marks the current book
                bookparser = argparse.ArgumentParser(prog='labb-book',description='Create a book or display existing books.')
                bookparser.add_argument('book',nargs='*')
                bookargs = bookparser.parse_args(mainargs.extra)

                try:
                        book_cmd(the_labb,bookargs.book)
                except LabbError as err:
                        print err.message
                        sys.exit(1)

        try: #are there any books? if not, these remaining commands can't be useful.
                check_for_books(the_labb)
        except LabbError as err:
                print err.message
                sys.exit(1)
                
        if mainargs.cmd == 'entry': #'entry' creates a new entry. takes no extra arguments.
                entryparser = argparse.ArgumentParser(prog='labb-entry',description='Open new entry in the current book.')
                entryargs = entryparser.parse_args(mainargs.extra)

                try:
                        entry_cmd(the_labb)
                except LabbError as err:
                        print err.message
                        sys.exit(1)

        if mainargs.cmd == 'close': #if there is an open entry, this closes it.
                closeparser = argparse.ArgumentParser(prog='labb-close',description='Close an open entry in the current book.')
                closeargs = closeparser.parse_args(mainargs.extra)

                try:
                        close_cmd(the_labb)
                except LabbError as err:
                        print err.message
                        sys.exit(1)

        if mainargs.cmd == 'add': #if there is an open entry, we can add data to it. requires the data type as an additional argument, as well as a filename, if relevant.
                addparser = argparse.ArgumentParser(prog='labb-add',description='Add data to an open entry in the current book.')
                addparser.add_argument('datatype',choices=['note','equation','citation','image'])
                addparser.add_argument('filename',nargs='?',default=None)
                addargs = addparser.parse_args(mainargs.extra)

                try:
                        add_cmd(the_labb,addargs)
                except LabbError as err:
                        print err.message
                        sys.exit(1)

        if mainargs.cmd == 'tag': #if there's an open entry, we can add a tag to it. requires the tag string as an additional argument.
                tagparser = argparse.ArgumentParser(prog='labb-tag',description='Add a tag to an open entry in the current book.')
                tagparser.add_argument('text',nargs=1)
                tagargs = tagparser.parse_args(mainargs.extra)

                try:
                        add_tag_cmd(the_labb,tagargs)
                except LabbError as err:
                        print err.message
                        sys.exit(1)

        if mainargs.cmd == 'show':
                showparser = argparse.ArgumentParser(prog='labb-show',description='Display the contents of a book.')
                showparser.add_argument('book',nargs='+')
                showargs = showparser.parse_args(mainargs.extra)

                try:
                        show_cmd(the_labb,showargs)
                except LabbError as err:
                        print err.message
                        sys.exit(1)

        if mainargs.cmd == 'export': #takes a book name as an additional argument, and exports it using labb's export_book method.
                exportparser = argparse.ArgumentParser(prog='labb-export',description='Export a book.')
                exportparser.add_argument('book',nargs='+')
                exportparser.add_argument('format_type',nargs='+')
                exportargs = exportparser.parse_args(mainargs.extra)

                try:
                        export_cmd(the_labb,exportargs)
                except LabbError as err:
                        print err.message
                        sys.exit(1)
