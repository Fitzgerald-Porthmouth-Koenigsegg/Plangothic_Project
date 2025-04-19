import os
import subprocess
import glob
import zipfile
import sys
import shutil
from multiprocessing import Pool, cpu_count

# 获取脚本所在的绝对路径，并切换工作目录到脚本所在位置
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

def extract_ufoz(ufoz_path):
    """从 ufoz 文件中仅提取.ufo目录"""
    with zipfile.ZipFile(ufoz_path, 'r') as zip_ref:
        # 在zip文件中查找所有.ufo目录
        ufo_dirs = [f for f in zip_ref.namelist() if f.endswith('.ufo/') or f.endswith('.ufo\\')]
        if not ufo_dirs:
            # 尝试查找没有尾部斜杠的.ufo条目
            ufo_dirs = [f for f in zip_ref.namelist() if f.endswith('.ufo')]

        if not ufo_dirs:
            raise Exception(f"在 {ufoz_path} 中未找到.ufo目录")

        # 获取基础目录名称
        ufo_dir = ufo_dirs[0].rstrip('/').rstrip('\\')

        # 仅提取所需文件（.ufo目录中的所有文件）
        for file in zip_ref.namelist():
            if file.startswith(ufo_dir):
                zip_ref.extract(file, '.')

    return ufo_dir

def process_ufoz_file(ufoz_file):
    """处理单个 ufoz 文件并转换为 TTF"""
    try:
        target_dir = os.path.abspath("../build")
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        # 提取 ufoz 文件
        ufo_dir = extract_ufoz(ufoz_file)

        # 使用 fontmake 转换为 TTF
        fontname = os.path.basename(os.path.splitext(ufoz_file)[0])
        cmd = [
            "fontmake", "-u", ufo_dir, 
            "--keep-overlaps", "--keep-direction",
            "--no-generate-GDEF", "--no-production-names",
            "-o", "ttf"
        ]
        subprocess.run(cmd, check=True)

        # 将 TTF 文件移动到目标目录
        ttf_file = f"master_ttf/{fontname}.ttf"
        if os.path.exists(ttf_file):
            shutil.move(ttf_file, os.path.join(target_dir, f"{fontname}.ttf"))
        else:
            # 备用方案：同时检查instance_ttf，以防万一
            ttf_file = f"instance_ttf/{fontname}.ttf"
            if os.path.exists(ttf_file):
                shutil.move(ttf_file, os.path.join(target_dir, f"{fontname}.ttf"))

        # 清理
        if os.path.exists(ufo_dir):
            shutil.rmtree(ufo_dir)
        if os.path.exists("instance_ttf"):
            shutil.rmtree("instance_ttf")
        if os.path.exists("master_ttf"):
            shutil.rmtree("master_ttf")

        return f"成功处理 {ufoz_file}"
    except Exception as e:
        return f"处理 {ufoz_file} 时出错: {str(e)}"

def main():
    # 获取所有 ufoz 文件
    ufoz_files = glob.glob("*.ufoz")

    if not ufoz_files:
        print("当前目录中未找到.ufoz文件")
        return

    # 确定要使用的进程数（最多10个）
    num_processes = min(len(ufoz_files), cpu_count(), 10)

    print(f"找到 {len(ufoz_files)} 个.ufoz文件，使用 {num_processes} 个进程")

    # 并行处理文件
    with Pool(processes=num_processes) as pool:
        results = pool.map(process_ufoz_file, ufoz_files)

    # 打印结果
    for result in results:
        print(result)

if __name__ == "__main__":
    main()