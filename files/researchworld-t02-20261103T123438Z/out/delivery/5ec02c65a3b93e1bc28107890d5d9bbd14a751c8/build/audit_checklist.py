#!/usr/bin/env python3
"""Compare a filled NeurIPS checklist with its unchanged official source."""
import argparse
import hashlib
import json
import re
from pathlib import Path

START = '%%% BEGIN INSTRUCTIONS %%%'
END = '%%% END INSTRUCTIONS %%%'
ANSWER = r'\\item\[\]\s*Answer:'
JUSTIFICATION = r'\\item\[\]\s*Justification:'
GUIDELINES = r'\\item\[\]\s*Guidelines:'


def remove_instructions(text):
    if START in text and END in text:
        left, tail = text.split(START, 1)
        return left + tail.split(END, 1)[1]
    return text


def uncomment(text):
    return re.sub(r'(?<!\\)%[^\n]*', '', text)


def structure(text):
    text = uncomment(remove_instructions(text))
    text = re.sub(ANSWER + r'.*?(?=' + JUSTIFICATION + ')',
                  lambda _: r'\item[] Answer: ANSWER ', text, flags=re.S)
    text = re.sub(JUSTIFICATION + r'.*?(?=' + GUIDELINES + ')',
                  lambda _: r'\item[] Justification: JUSTIFICATION ', text, flags=re.S)
    return re.sub(r'\s+', ' ', text).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, default=Path('venue/official/checklist.tex'))
    parser.add_argument('--checklist', type=Path, default=Path('manuscript/checklist.tex'))
    parser.add_argument('--output', type=Path, default=Path('build/checklist-audit.json'))
    args = parser.parse_args()
    for path in (args.reference, args.checklist):
        if not path.is_file():
            parser.error(f'Missing checklist input: {path}')
    reference = args.reference.read_text()
    completed = args.checklist.read_text()
    body = uncomment(remove_instructions(completed))
    answers = re.findall(ANSWER + r'(.*?)(?=' + JUSTIFICATION + ')', body, re.S)
    justifications = re.findall(JUSTIFICATION + r'(.*?)(?=' + GUIDELINES + ')', body, re.S)
    problems = []
    if START in completed or END in completed:
        problems.append('Remove the official instruction block and its markers.')
    if structure(reference) != structure(completed):
        problems.append('Checklist structure/wording differs outside answers and justifications.')
    if len(answers) != 16 or len(justifications) != 16 or body.count('Question:') != 16:
        problems.append('Need all 16 questions, answers and justifications.')
    for i, answer in enumerate(answers, 1):
        if not re.fullmatch(r'\s*\\answer(?:Yes|No|NA)\{\}\s*', answer):
            problems.append(f'Question {i}: use exactly one provided Yes/No/NA answer macro.')
    for i, justification in enumerate(justifications, 1):
        if not justification.strip() or re.search(r'\\justificationTODO\b', justification):
            problems.append(f'Question {i}: missing actual justification.')
    result = {
        'reference': str(args.reference), 'checklist': str(args.checklist),
        'reference_sha256': hashlib.sha256(args.reference.read_bytes()).hexdigest(),
        'checklist_sha256': hashlib.sha256(args.checklist.read_bytes()).hexdigest(),
        'questions': body.count('Question:'), 'answers': len(answers),
        'technical_checks_passed': not problems, 'problems': problems,
        'scope': 'Checks preserved source wording and filled fields. Evidence support, answer accuracy, 1–2 sentence justifications and PDF rendering require independent inspection.',
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    raise SystemExit(1 if problems else 0)


if __name__ == '__main__':
    main()
