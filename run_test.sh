rm -rf .labb/
./labb.py init ./labb_setup
echo 'A test book' | ./labb.py book kitab
./labb.py book
./labb.py entry
echo 'Just a note' | ./labb.py add note
echo '1=2' | ./labb.py add equation
echo 'Just a caption' | ./labb.py add image test.png
./labb.py tag cats
./labb.py tag dogs
./labb.py close
./labb.py show kitab
./labb.py export kitab tex
./labb.py export kitab md
