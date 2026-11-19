"""Frozen 4 x 4 instruction/format bank; no outcome-dependent prompt generation."""
import json,hashlib

INSTRUCTIONS=[
 'Solve the multiple-choice question. Respond with only the letter of the correct answer.',
 'Choose the best answer to the question below. Return only its option letter, without explanation.',
 'Read the question carefully and evaluate all answer choices. Output just the single letter identifying the correct choice.',
 'You are taking a knowledge exam. Select the most accurate option. Your entire response must be its capital letter.',
]
FORMATS=[('dot','Question:\n','\nOptions:\n','\nAnswer:'),
 ('parenthesis','','\n','\nThe correct option is:'),
 ('colon','Problem: ','\nChoices:\n','\nSelected letter:'),
 ('bracket','Multiple-choice question\n','\nPossible answers\n','\nFinal answer:')]
BANK=[dict(id=4*i+j,instruction_index=i,format_index=j,instruction=instruction,format=fmt[0]) for i,instruction in enumerate(INSTRUCTIONS) for j,fmt in enumerate(FORMATS)]
BANK_SHA256=hashlib.sha256(json.dumps(BANK,sort_keys=True).encode()).hexdigest()

def render(row,candidate):
 c=BANK[candidate];name,prefix,sep,cue=FORMATS[c['format_index']]
 def label(i):
  letter=chr(65+i)
  return {'dot':f'{letter}.','parenthesis':f'({letter})','colon':f'{letter}:','bracket':f'[{letter}]'}[name]
 q=prefix+row['question']+sep+'\n'.join(f'{label(i)} {x}' for i,x in enumerate(row['options']))+cue
 return '<|im_start|>system\nYou are a helpful assistant. '+c['instruction']+'<|im_end|>\n<|im_start|>user\n'+q+'<|im_end|>\n<|im_start|>assistant\n'

if __name__=='__main__':print(json.dumps(dict(bank_sha256=BANK_SHA256,candidates=BANK),indent=2))
