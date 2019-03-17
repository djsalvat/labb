#!/usr/bin/python

from os import path, isatty
import argparse
import sys
import subprocess
from datetime import datetime
import json

class LabbError(Exception):
    '''Base class for labb exceptions.'''
    pass

class datum(dict):
    def __init__(self,data_type='note',text='',filename=None):
        self.__dict__.update({k:v for k,v in locals().items() if k!='self'})
        dict.__init__(self,self.__dict__)

class entry(dict):
    '''Entry objects are appended to the entry list in the book class. They are 'open' when they are first added to the list.
They contain a data list which can be appended until the entry is closed.'''
    def __init__(self,timestamp):
        self.data = []
        self.timestamp = timestamp
        self.tags = []
        dict.__init__(self,self.__dict__)

class book(dict):
    '''A book requires an introduction from the user, as well as an author and name. A directory is created in .labb to store files associated with data.
It contains a list of entries, as well as methods to open a new entry, add data to a current entry, and close an entry.'''
    def __init__(self,name,introduction):
        self.__dict__.update({k:v for k,v in locals().items() if k!='self'})
        self.directory = '.labb/books/' + name
        self.entries = []
        self.is_open = False
        dict.__init__(self,self.__dict__)

class labb(dict):
    '''A labb consists of a dictionary of books -- it associates a book's name with the book object.
Has methods to create new books, and fetch existing books. labb.current stores the name of the book to which one can submit new entries.'''
    def __init__(self,author):
        self.books = {}
        self.author = author
        self.current = None 
        dict.__init__(self,self.__dict__)

def get_from_editor(initial=''):
    '''Method that opens vim, and saves a dummy text file. The contents of the dummy file are returned as a string. This is used by data types that need string input.'''
    from tempfile import NamedTemporaryFile
    with NamedTemporaryFile(delete=False) as tf: #create a temp file
        tfName = tf.name
        tf.write(initial)

    if subprocess.call(['vim',tfName]) != 0: #did vim succesfully close?
        raise LabbError('Vim did not successfully close.')

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

def update_self(s):
    s.update(s.__dict__)

def update_labb(labb):
    for bn,bk in labb.books.iteritems():
        for ent in bk.entries:
            update_self(ent)
        update_self(bk)
    update_self(labb)
    return labb

def save_labb(the_labb):
    updated_labb = update_labb(the_labb)
    with open('.labb/labb.json','wb') as outfile:
        json.dump(updated_labb,outfile)

def build_labb(labb_json):
    the_labb = labb(labb_json['author'])
    the_labb.current = labb_json['current'] 
    for book_name,the_book in labb_json['books'].iteritems():
        the_labb.books[book_name] = book(the_book['name'],the_book['introduction'])
        the_labb.books[book_name].is_open = the_book['is_open']
        the_labb.books[book_name].directory = the_book['directory']
        for entry_json in the_book['entries']:
            the_labb.books[book_name].entries.append(entry(entry_json['timestamp']))
            the_labb.books[book_name].entries[-1].data = [datum(data_type=datum_json['data_type'],text=datum_json['text'],filename=datum_json['filename']) for datum_json in entry_json['data']]
            the_labb.books[book_name].entries[-1].tags = entry_json['tags']
    return the_labb

def open_labb():
    if not path.exists('.labb/labb.json'):
        raise LabbError('You have not yet initialized labb.')
    else:
        with open('.labb/labb.json','rb') as infile:
            the_labb_json = json.load(infile)
        the_labb = build_labb(the_labb_json)
        return the_labb

class LabbCommands:
    @staticmethod
    def init(args):
        if path.exists('.labb/labb.json'):
            raise LabbError('Already initialized in current directory.')
        if len(args)!=1:
            raise LabbError('labb-init expects one argument.')
        else:
            setup_path = args[0]
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
                    subprocess.call(['cp',setup_path+'/'+ft+'/'+fn,'.labb/'+ft+'/'])
            author = raw_input('Type the author name: ')
            initial_labb = labb(author)
            save_labb(initial_labb)
            print 'Labb initialized'

    @staticmethod
    def book(args):
        the_labb = open_labb()
        if len(args) == 0:
            for a_book in the_labb.books.keys():
                if the_labb.current == a_book:
                    if not the_labb.books[a_book].is_open:
                        print a_book+' *'
                    else:
                        print a_book+' *o'
                else:
                    print a_book

        elif len(args) == 1:
            book_name = args[0]
            if book_name not in the_labb.books:
                book_introduction = process_input()
                subprocess.call(['mkdir','.labb/books/'+book_name])
                the_labb.books[book_name] = book(book_name,book_introduction)
                print 'New book '+book_name+' created.'
            the_labb.current = book_name
            print 'Current book changed to '+the_labb.current+'.'
            save_labb(the_labb)
        else:
            raise LabbError('Specify at most one book.')

    @staticmethod
    def entry(args):
        the_labb = open_labb()
        if the_labb.books[the_labb.current].is_open:
            raise LabbError('There is already an open entry.')
        else:
            timestamp = datetime.utcnow().isoformat()
            the_labb.books[the_labb.current].entries.append(entry(timestamp))
            the_labb.books[the_labb.current].is_open = True
            save_labb(the_labb)
            print 'New entry opened in '+the_labb.books[the_labb.current].name+'.'

    @staticmethod
    def close(args):
        the_labb = open_labb()
        if the_labb.books[the_labb.current].is_open:
            the_labb.books[the_labb.current].is_open = False
            save_labb(the_labb)
        else:
            raise LabbError('This book does not have an open entry.')

    @staticmethod
    def add(args):
        the_labb = open_labb()
        if not the_labb.books[the_labb.current].is_open:
            raise LabbError('There is no open entry.')
        if len(args)==0:
            raise LabbError('Specify a data type.')
        elif len(args)==1:
            fn = None
        else:
            fn = args[1]
            if not path.exists(fn):
                raise LabbError('File does not exist.')
            subprocess.call(['cp',fn,the_labb.books[the_labb.current].directory+'/'])
        data_type = args[0]
        new_filename = fn if fn is None else the_labb.books[the_labb.current].directory+'/'+path.basename(fn)
        the_labb.books[the_labb.current].entries[-1].data.append(datum(data_type=data_type,text=process_input(),filename=new_filename))
        save_labb(the_labb)

    @staticmethod
    def tag(args):
        the_labb = open_labb()
        if not the_labb.books[the_labb.current].is_open:
            raise LabbError('There is no open entry.')
        if len(args)==0:
            raise LabbError('Supply a tag name.')
        the_labb.books[the_labb.current].entries[-1].tags.append(args[0])
        save_labb(the_labb)

    @staticmethod
    def export(args):
        if len(args)!=2:
            raise LabbError('Supply a book name and export format.')
        book_name, format_type = args
        the_labb = open_labb()

        if book_name not in the_labb.books:
            raise LabbError('Book not found.')

        the_book = the_labb.books[book_name]

        export_filename = the_book.name+'.'+format_type
        export_file = open(export_filename,'w')

        #retrieve the format

        format_dict = {}

        for doc in ['intro','entry','note','equation','citation','image','tags','outro']:
            with open('.labb/'+format_type+'/'+doc) as f:
                format_dict[doc] = f.read()

        export_file.write(format_dict['intro'] % {'name': the_book.name,'author': the_labb.author,'intro': the_book.introduction})

        #now loop over entries and make sections for each.

        for ent in the_book.entries:
            export_file.write(format_dict['entry'] % {'timestamp' : ent.timestamp})

            for dat in ent.data:
                export_file.write(format_dict[dat.data_type] % dat)

            tagstring = ', '.join([t for t in ent.tags])

            export_file.write(format_dict['tags'] % {'tags': tagstring})

        export_file.write(format_dict['outro']) #close the document.
        export_file.close()

        print 'Book '+book_name+' exported.'

    @staticmethod
    def show(args):
        if len(args)==0:
            raise LabbError('Specify a book.')
        book_name = args[0]
        the_labb = open_labb()
        if book_name not in the_labb.books:
            raise LabbError('Book not found.')

        the_book = the_labb.books[book_name]

        print the_book.name
        print the_labb.author+'\n'
        print the_book.introduction+'\n'

        for ent in the_book.entries:
            print ent.timestamp

            for datum in ent.data:
                if datum.filename is not None:
                    print '<<'+datum.filename+'>>'
                print datum.text+'\n'

            print 'Tags:'
            for tag in ent.tags:
                print tag

if __name__ == '__main__':
    #when executed, labb.py is a command to manipulate a labb object, which is saved in a hidden directory .labb
    mainparser = argparse.ArgumentParser(prog='labb',description='A simple command-line logbook.') #create the parser
    mainparser.add_argument('--version', action='version', version='Current version is 0.1.')
    mainparser.add_argument('cmd',choices=['init','book','show','entry','add','tag','close','export']) #the possible commands to perform
    mainparser.add_argument('extra',nargs='*') #some commands require extra arguments
    mainargs = mainparser.parse_args() #this line actuall parses argv and returns the data to args

    getattr(LabbCommands,mainargs.cmd)(mainargs.extra)
