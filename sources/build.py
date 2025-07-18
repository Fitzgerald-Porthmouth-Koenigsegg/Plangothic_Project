import os
import subprocess
import glob
import zipfile
import sys
import shutil
from multiprocessing import Pool, cpu_count

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

def extract_ufoz(ufoz_path):
    with zipfile.ZipFile(ufoz_path, 'r') as zip_ref:
        ufo_dirs = [f for f in zip_ref.namelist() if f.endswith('.ufo/') or f.endswith('.ufo\\')]
        if not ufo_dirs:
            ufo_dirs = [f for f in zip_ref.namelist() if f.endswith('.ufo')]

        if not ufo_dirs:
            raise Exception(f"在 {ufoz_path} 中未找到.ufo目录")

        ufo_dir = ufo_dirs[0].rstrip('/').rstrip('\\')

        for file in zip_ref.namelist():
            if file.startswith(ufo_dir):
                zip_ref.extract(file, '.')

    return ufo_dir

def process_ufoz_file(ufoz_file):
    try:
        target_dir = os.path.abspath("../build")
        os.makedirs(target_dir, exist_ok=True)

        ufo_dir = extract_ufoz(ufoz_file)

        cmd = [
            "fontmake", "-u", ufo_dir, 
            "--keep-overlaps", "--keep-direction",
            "--no-generate-GDEF", "--no-production-names",
            "--optimize-cff", "0", "--cff-round-tolerance", "0.01",
            "-o", "ttf", "--output-dir", target_dir
        ]
        subprocess.run(cmd, check=True)

        if os.path.exists(ufo_dir):
            shutil.rmtree(ufo_dir)

        return f"成功处理 {ufoz_file}"
    except Exception as e:
        return f"处理 {ufoz_file} 时出错: {str(e)}"

def main():
    ufoz_files = glob.glob("*.ufoz")

    if not ufoz_files:
        print("当前目录中未找到.ufoz文件")
        return

    num_processes = min(len(ufoz_files), cpu_count(), 10)

    print(f"找到 {len(ufoz_files)} 个.ufoz文件，使用 {num_processes} 个进程")

    with Pool(processes=num_processes) as pool:
        results = pool.map(process_ufoz_file, ufoz_files)

    for result in results:
        print(result)

if __name__ == "__main__":
    main()
