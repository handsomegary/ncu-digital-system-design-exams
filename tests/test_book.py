"""Check the public question/solution index and compile the code extracted from the answers."""
import json
import hashlib
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]


def main():
    book=json.loads((ROOT/'index.json').read_text(encoding='utf-8'))
    assert len(book['exams'])==5 and book['question_count']==27, 'Retained scope changed; update the documented inventory'
    count=0
    with tempfile.TemporaryDirectory(prefix='dsd_book_') as name:
        temporary=Path(name)
        for entry in book['exams']:
            questions=(ROOT/entry['questions']).read_text(encoding='utf-8')
            assert questions.strip(), 'No question text'
            latex=ROOT/entry['question_latex']
            assert latex.is_file() and '\\begin{document}' in latex.read_text(encoding='utf-8'), 'Missing editable LaTeX'
            if entry.get('original_exam'):
                original=ROOT/entry['original_exam']
                metadata=json.loads((original.parent/'metadata.json').read_text(encoding='utf-8'))
                assert hashlib.sha256(original.read_bytes()).hexdigest()==metadata['original_sha256'], 'Original source PDF changed'
            answer=(ROOT/entry['solutions']).read_text(encoding='utf-8')
            code=answer.split('<!-- SOLUTION_CODE_BEGIN -->')[1].split('<!-- SOLUTION_CODE_END -->')[0]
            blocks=dict(re.findall(r'### `([^`]+)`\s+```\w+\n(.*?)\n```',code,re.S))
            assert set(blocks)=={Path(p).name for p in entry['sources']}, 'Missing full code in answer'
            folder=temporary/str(entry['year'])
            folder.mkdir()
            files=[]
            for source in entry['sources']:
                path=ROOT/source
                text=blocks[path.name]+'\n'
                assert text==path.read_text(encoding='utf-8').rstrip()+'\n', source
                target=folder/path.name
                target.write_text(text,encoding='utf-8')
                if path.suffix in ['.v','.sv']: files.append(target)
                elif path.suffix=='.py': compile(text,str(target),'exec')
                count+=1
            result=subprocess.run([os.environ.get('IVERILOG','iverilog'),'-g2012','-Wall','-t','null',*map(str,files)],cwd=folder,text=True,capture_output=True,timeout=60)
            assert result.returncode==0, result.stdout+result.stderr
    originals={entry['original_exam'] for entry in book['exams'] if entry.get('original_exam')}
    assert len(originals)==4 and 'exams/2008/original.pdf' not in originals, 'Unexpected source PDF inventory'
    forbidden={'.vcd','.fst','.lxt','.lxt2','.vvp','.pdf','.png','.jpg','.jpeg','.zip'}
    public=subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines()
    assert not [p for p in public if Path(p).suffix.lower() in forbidden and p not in originals], 'Generated artifacts in repo'
    assert all(not (ROOT/p).is_file() or (ROOT/p).stat().st_size<(2000000 if p in originals else 300000) for p in public), 'Unexpected large public file'
    print(f'PASS: 5 question sets, 27 questions, {count} complete embedded source files; 4 verified original PDFs and 5 LaTeX transcriptions; no generated wave/image artifacts')


if __name__=='__main__': main()
