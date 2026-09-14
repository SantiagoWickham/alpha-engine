from pathlib import Path
import tarfile, shutil
archive=Path(__file__).resolve().parents[1]/'cloud'/'runtime'/'alpha_engine_runtime.tar.gz'
dest=Path(r'C:\Users\santi\OneDrive\Escritorio\ALPHA_ENGINE_V12_RETURN_FIRST')
if dest.exists(): shutil.rmtree(dest)
dest.mkdir(parents=True,exist_ok=True)
with tarfile.open(archive,'r:gz') as tf:
    tf.extractall(dest)
print('RUNTIME_EXTRACT: PASS')
print(dest)
