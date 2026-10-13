"""Embed source text in each solution; keep the public index small and link-based."""
import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BEGIN='<!-- SOLUTION_CODE_BEGIN -->'
END='<!-- SOLUTION_CODE_END -->'


def generated():
    writes={}
    index=[]
    folders=sorted(p for p in (ROOT/'exams').iterdir() if p.is_dir())
    for folder in folders:
        metadata=json.loads((folder/'metadata.json').read_text(encoding='utf-8'))
        question=folder/metadata['question_document']
        question_latex=folder/metadata['question_latex']
        original_exam=folder/metadata['original_exam']
        document=folder/metadata['solution_document']
        assert question.is_file(), f'Missing questions: {folder.name}'
        assert question_latex.is_file() and original_exam.is_file(), f'Missing original/LaTeX: {folder.name}'
        assert metadata['question_count']>0, 'Do not retain answer-only years'
        text=document.read_text(encoding='utf-8')
        assert text.count(BEGIN)==text.count(END)==1, f'Missing/duplicate markers: {document}'
        declared=metadata['sources']
        assert len(declared)==len(set(declared)), f'Duplicate source: {folder.name}'
        assert {p.name for p in folder.glob('*.v')} <= set(declared), 'Every HDL source must be in the solution'
        code=[]
        for name in declared:
            path=(folder/name).resolve()
            assert path.parent==folder.resolve() and path.is_file(), f'Unexpected source: {name}'
            language={'.v':'verilog','.sv':'systemverilog','.py':'python'}.get(path.suffix,'text')
            code += [f'### `{name}`', '', f'```{language}', path.read_text(encoding='utf-8').rstrip(), '```', '']
        before,rest=text.split(BEGIN)
        _,after=rest.split(END)
        writes[document]=before+BEGIN+'\n\n'+'\n'.join(code)+'\n'+END+after
        index.append({'year':metadata['year'],'exam':metadata['exam'],'question_count':metadata['question_count'],
                      'questions':question.relative_to(ROOT).as_posix(),
                      'question_latex':question_latex.relative_to(ROOT).as_posix(),
                      'original_exam':original_exam.relative_to(ROOT).as_posix(),
                      'solutions':document.relative_to(ROOT).as_posix(),
                      'sources':[(folder/name).relative_to(ROOT).as_posix() for name in declared]})
    assert index, 'No retained questions'
    writes[ROOT/'index.json']=json.dumps({'question_count':sum(p['question_count'] for p in index),'exams':index},ensure_ascii=False,indent=2)+'\n'
    return writes,index


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    writes,index=generated()
    stale=[]
    for path,text in writes.items():
        if not path.exists() or path.read_text(encoding='utf-8')!=text:
            if args.check: stale.append(path.relative_to(ROOT).as_posix())
            else: path.write_text(text,encoding='utf-8',newline='\n')
    if stale: raise SystemExit('Out of sync: '+', '.join(stale))
    print(f'{len(index)} exam sets / {sum(p["question_count"] for p in index)} questions: '+('in sync' if args.check else 'updated'))


if __name__=='__main__': main()
