#!/usr/bin/env fontforge
import fontforge
import os
import glob
import zipfile
import shutil
from multiprocessing import Pool, cpu_count

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

def extract_ufoz(ufoz_path):
    """解压 .ufoz 文件并返回 .ufo 目录路径"""
    with zipfile.ZipFile(ufoz_path, 'r') as zip_ref:
        ufo_dirs = [f for f in zip_ref.namelist() 
                    if f.endswith('.ufo/') or f.endswith('.ufo\\') or f.endswith('.ufo')]

        if not ufo_dirs:
            raise Exception(f"在 {ufoz_path} 中未找到 .ufo 目录")

        ufo_dir = ufo_dirs[0].rstrip('/').rstrip('\\')

        for file in zip_ref.namelist():
            if file.startswith(ufo_dir):
                zip_ref.extract(file, '.')

    return ufo_dir

def process_ufoz_file(ufoz_file):
    """处理单个 .ufoz 文件：解压 -> 生成 TTF -> 清理"""
    try:
        target_dir = os.path.abspath("../build")
        os.makedirs(target_dir, exist_ok=True)

        ufo_dir = extract_ufoz(ufoz_file)

        font = fontforge.open(ufo_dir)

        base_name = os.path.splitext(os.path.basename(ufoz_file))[0]
        output_path = os.path.join(target_dir, f"{base_name}.ttf")

        font.generate(output_path, flags=('opentype'))
        font.close()

        if os.path.exists(ufo_dir):
            shutil.rmtree(ufo_dir)

        return f"✓ 成功处理 {ufoz_file} -> {output_path}"

    except Exception as e:
        return f"✗ 处理 {ufoz_file} 时出错: {str(e)}"

def main():
    ufoz_files = glob.glob("*.ufoz")

    if not ufoz_files:
        print("当前目录中未找到 .ufoz 文件")
        return

    num_processes = min(len(ufoz_files), cpu_count(), 10)
    print(f"找到 {len(ufoz_files)} 个 .ufoz 文件，使用 {num_processes} 个进程")

    with Pool(processes=num_processes) as pool:
        results = pool.map(process_ufoz_file, ufoz_files)

    for result in results:
        print(result)

if __name__ == "__main__":
    main()
