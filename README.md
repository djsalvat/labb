# labb
### a text-based logbook

## Intro
A repository consists of a set of named books,  
which in turn contains a list of entries.  
Each entry can contain text, latex equations,  
images, code blocks (not implemented yet),  
and citations. Tags can be added to entries  
for future implementation of a tag search.

## Usage
An install script is still being developed.  
Basic usage is

    labb init
    
Which will prompt you for an author.

    labb book mybook
    
Will create a new book, and will  
open vim for you to type an introduction.

    labb book
    
Will show a list of all books,  
with a \* after the current book.  
If the current book has an unclosed entry,  
there will be \*o after the book.

Entries are opened with

    labb entry
    
which can only succeed if there is not  
already a current entry.  
Then one can add content to the entry:

    labb add note
    
which will open vim for the note to be typed.

    labb add image [filename]
    
which will copy the image file to the labb  
repository, and open vim for you to type  
a caption.
