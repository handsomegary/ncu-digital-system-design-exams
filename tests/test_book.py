"""Check the public question/solution index and compile the code extracted from the answers."""
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]


def main():
    book=json.loads((ROOT/'index.json').read_text(encoding='utf-8'))
    assert len(book['exams'])==4 and book['question_count']==21, 'Retained scope changed; update the documented inventory'
    count=0
    with tempfile.TemporaryDirectory(prefix='dsd_book_') as name:
        temporary=Path(name)
        for entry in book['exams']:
            questions=(ROOT/entry['questions']).read_text(encoding='utf-8')
            assert questions.strip(), 'No question text'
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
    forbidden={'.vcd','.fst','.lxt','.lxt2','.vvp','.pdf','.png','.jpg','.jpeg','.zip'}
    public=subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines()
    assert not [p for p in public if Path(p).suffix.lower() in forbidden], 'Generated artifacts in repo'
    assert all(not (ROOT/p).is_file() or (ROOT/p).stat().st_size<300000 for p in public), 'Unexpected large public file'
    print(f'PASS: 4 question sets, 21 questions, {count} complete embedded source files; no wave/image artifacts')


if __name__=='__main__': main()
