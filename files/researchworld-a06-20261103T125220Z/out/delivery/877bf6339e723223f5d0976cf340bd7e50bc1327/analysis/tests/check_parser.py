import sys
sys.path.insert(0,'scripts')
from run_real import parse_answer
for text,expected in [('A','A'),(' (C). ','C'),('[J]','J'),('B.','B'),('The answer is A',None),('A or B',None),('K',None),('',None),('a',None)]:
 assert parse_answer(text)==expected,(text,expected)
print('PASS: strict parser accepts declared forms, rejects extra text, multiple answers and non-bank letters.')
