from pathlib import Path
import hashlib, sys
root=Path(__file__).resolve().parents[1]/'cloud'/'runtime'
parts=sorted(root.glob('alpha_engine_runtime.tar.gz.part-*'))
if not parts: raise SystemExit('No runtime parts found')
out=root/'alpha_engine_runtime.tar.gz'
h=hashlib.sha256()
with out.open('wb') as w:
    for p in parts:
        with p.open('rb') as r:
            while True:
                b=r.read(1024*1024)
                if not b: break
                w.write(b); h.update(b)
print('RUNTIME_REASSEMBLE: PASS')
print('parts:',len(parts),'bytes:',out.stat().st_size,'sha256:',h.hexdigest())
