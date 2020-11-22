#!/usr/bin/env python

from os import path, isatty
import argparse
import sys
import subprocess
from datetime import datetime
import json
from tempfile import NamedTemporaryFile
from dataclasses import dataclass,field

class LabbError(Exception):
    pass

formats = ['tex','md']
format_types = ['intro','note','citation','image','entry','equation','tags','outro']

@dataclass
class Datum:
    type: str = ''
    text: str = ''
    filename: str = ''

@dataclass
class Entry:
    timestamp: str = ''
    data: list = field(default_factory=list)
    tags: list = field(default_factory=list)

@dataclass
class Book:
    name: str = ''
    introduction: str = ''
    entries: list = field(default_factory=list)

@dataclass
class Labb:
    author: str = ''
    books: dict = field(default_factory=dict)
    current: str = ''
    is_open: bool = False

class LabbEncoder(json.JSONEncoder):
    def default(self,obj):
        if any([isinstance(obj,t) for t in [Labb,Book,Entry,Datum]]):
            return obj.__dict__
        else:
            return json.JSONEncoder.default(self,obj)

    @staticmethod
    def as_labb(obj):
        for LabbType in [Labb,Book,Entry,Datum]:
            if LabbType().__dict__.keys() == obj.keys():
                return LabbType(**obj)
        return obj

def get_from_editor(initial=''):
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

def save_labb(the_labb):
    with open('.labb/labb.json','w') as outfile:
        json.dump(the_labb,outfile,cls=LabbEncoder)

def open_entry(book_name,entry_timestamp):
    with open('.labb/books/{0}/{1}/{1}.json'.format(book_name,entry_timestamp),'r') as entryfile:
        return json.load(entryfile,object_hook=LabbEncoder.as_labb)

def update_entry_data(book_name,entry_timestamp,datum):
    with open('.labb/books/{0}/{1}/{1}.json'.format(book_name,entry_timestamp),'r') as entryfile:
        entry = json.load(entryfile,object_hook=LabbEncoder.as_labb)
    entry.data.append(datum)
    with open('.labb/books/{0}/{1}/{1}.json'.format(book_name,entry_timestamp),'w') as entryfile:
        json.dump(entry,entryfile,cls=LabbEncoder)

def update_tag(book_name,entry_timestamp,tag):
    with open('.labb/books/{0}/{1}/{1}.json'.format(book_name,entry_timestamp),'r') as entryfile:
        entry = json.load(entryfile,object_hook=LabbEncoder.as_labb)
        entry.tags.append(tag)
    with open('.labb/books/{0}/{1}/{1}.json'.format(book_name,entry_timestamp),'w') as entryfile:
        json.dump(entry,entryfile,cls=LabbEncoder)

def open_labb():
    if not path.exists('.labb/labb.json'):
        raise LabbError('You have not yet initialized labb.')
    else:
        with open('.labb/labb.json','r') as infile:
            the_labb = json.load(infile,object_hook=LabbEncoder.as_labb)
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
            for ft in formats:
                subprocess.call(['mkdir','.labb'+'/'+ft])
                for fn in format_types:
                    subprocess.call(['cp',setup_path+'/'+ft+'/'+fn,'.labb/'+ft+'/'])
            author = input('Author: ')
            save_labb(Labb(author,{},'',False))
            print('Labb initialized')

    @staticmethod
    def book(args):
        the_labb = open_labb()
        if len(args) == 0:
            for a_book in the_labb.books.keys():
                if the_labb.current == a_book:
                    print(a_book+' o' if the_labb.is_open else ' *')
                else:
                    print(a_book)

        elif len(args) == 1:
            book_name = args[0]
            if book_name not in the_labb.books:
                book_introduction = process_input(editor_initial='book introduction')
                subprocess.call(['mkdir','.labb/books/'+book_name])
                the_labb.books[book_name] = Book(book_name,book_introduction,[])
                print('New book '+book_name+' created.')
            the_labb.current = book_name
            print('Current book changed to '+the_labb.current+'.')
            save_labb(the_labb)
        else:
            raise LabbError('Specify at most one book.')

    @staticmethod
    def entry(args):
        the_labb = open_labb()
        if the_labb.is_open:
            raise LabbError('There is already an open entry.')
        else:
            timestamp = datetime.utcnow().isoformat()
            entry_path = '.labb/books/'+the_labb.current+'/'+timestamp
            subprocess.call(['mkdir',entry_path])
            with open('{0}/{1}.json'.format(entry_path,timestamp),'w') as entryfile:
                json.dump(Entry(timestamp,[],[]),entryfile,cls=LabbEncoder)
            the_labb.books[the_labb.current].entries.append(timestamp)
            the_labb.is_open = True
            save_labb(the_labb)
            print('New entry opened in '+the_labb.books[the_labb.current].name+'.')

    @staticmethod
    def close(args):
        the_labb = open_labb()
        if the_labb.is_open:
            the_labb.is_open = False
            save_labb(the_labb)
        else:
            raise LabbError('This book does not have an open entry.')

    @staticmethod
    def add(args):
        the_labb = open_labb()
        fn = ''
        if not the_labb.is_open:
            raise LabbError('There is no open entry.')
        if len(args)==0:
            raise LabbError('Specify a data type.')
        elif len(args)==1:
            fn = 'None'
        else:
            if not path.exists(args[1]):
                raise LabbError('File does not exist.')
            fn = '.labb/books/' \
                +the_labb.books[the_labb.current].name+'/' \
                +the_labb.books[the_labb.current].entries[-1]+'/'+args[1]
            subprocess.call(['cp',args[1],fn])
        data_type = args[0]
        update_entry_data(the_labb.books[the_labb.current].name,
                          the_labb.books[the_labb.current].entries[-1],
                          Datum(type=data_type,text=process_input(),filename=fn))

    @staticmethod
    def tag(args):
        the_labb = open_labb()
        if not the_labb.is_open:
            raise LabbError('There is no open entry.')
        if len(args)==0:
            raise LabbError('Supply a tag name.')
        update_tag(the_labb.books[the_labb.current].name,
                   the_labb.books[the_labb.current].entries[-1],
                   args[0])

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

        for doc in format_types:
            with open('.labb/'+format_type+'/'+doc) as f:
                format_dict[doc] = f.read()

        export_file.write(format_dict['intro'] % {'name': the_book.name,'author': the_labb.author,'intro': the_book.introduction})

        #now loop over entries and make sections for each.

        for timestamp in the_book.entries:
            ent = open_entry(the_book.name,timestamp)
            export_file.write(format_dict['entry'] % {'timestamp' : ent.timestamp})

            for dat in ent.data:
                export_file.write(format_dict[dat.type] % dat.__dict__)

            tagstring = ', '.join([t for t in ent.tags])

            export_file.write(format_dict['tags'] % {'tags': tagstring})

        export_file.write(format_dict['outro']) #close the document.
        export_file.close()

        print('Book '+book_name+' exported.')

    @staticmethod
    def show(args):
        if len(args)==0:
            raise LabbError('Specify a book.')
        book_name = args[0]
        the_labb = open_labb()
        if book_name not in the_labb.books:
            raise LabbError('Book not found.')

        the_book = the_labb.books[book_name]

        print(the_book.name)
        print(the_labb.author+'\n')
        print(the_book.introduction+'\n')

        for timestamp in the_book.entries:
            ent = open_entry(the_book.name,timestamp)
            print(ent.timestamp)

            for datum in ent.data:
                print('<<'+datum.filename+'>>')
                print(datum.text+'\n')

            print('Tags:')
            for tag in ent.tags:
                print(tag)

if __name__ == '__main__':
    #when executed, labb.py is a command to manipulate a labb object, which is saved in a hidden directory .labb
    mainparser = argparse.ArgumentParser(prog='labb',description='Labb is a command-line logbook.') #create the parser
    mainparser.add_argument('--version', action='version', version='The current version is 0.1.')
    mainparser.add_argument('cmd',choices=[k for k,v in LabbCommands.__dict__.items() if type(v)==staticmethod]) #any static method in LabbCommands is a possible command
    mainparser.add_argument('extra',nargs='*') #some commands require extra arguments
    mainargs = mainparser.parse_args() #this line actually parses argv and returns the data to args

    getattr(LabbCommands,mainargs.cmd)(mainargs.extra)
