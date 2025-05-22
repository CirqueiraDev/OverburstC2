import os
import tarfile
import subprocess

FILES = [
    "arc_gnu_2017.09_prebuilt_uclibc_le_arc700_linux_install.tar.gz",
    "cross-compiler-armv4l.tar.bz2",
    "cross-compiler-armv5l.tar.bz2",
    "cross-compiler-armv6l.tar.bz2",
    "cross-compiler-armv7l.tar.bz2",
    "cross-compiler-i486.tar.gz",
    "cross-compiler-i586.tar.bz2",
    "cross-compiler-i686.tar.bz2",
    "cross-compiler-m68k.tar.bz2",
    "cross-compiler-mips.tar.bz2",
    "cross-compiler-mipsel.tar.bz2",
    "cross-compiler-powerpc-440fp.tar.bz2",
    "cross-compiler-powerpc.tar.bz2",
    "cross-compiler-sh4.tar.bz2",
    "cross-compiler-sparc.tar.bz2",
    "cross-compiler-x86_64.tar.bz2"
]

BASE_URL = "http://mirailovers.io/HELL-ARCHIVE/COMPILERS/"
DOWNLOAD_DIR = "compilers"
EXTRACT_DIR = "compilers_extracted"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(EXTRACT_DIR, exist_ok=True)

def download_file(filename):
    url = f"{BASE_URL}{filename}"
    output_path = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(output_path):
        print(f"[+] Já existe: {filename}")
        return output_path

    print(f"[i] Baixando: {filename}")
    cmd = (
        f'wget --quiet --show-progress --progress=bar:force '
        f'--referer="{BASE_URL}" '
        f'--user-agent="Mozilla/5.0" '
        f'-O "{output_path}" "{url}"'
    )
    os.system(cmd)
    return output_path

def extract_file(file_path):
    file_name = os.path.basename(file_path)
    extract_path = os.path.join(EXTRACT_DIR, file_name.replace(".tar.gz", "").replace(".tar.bz2", ""))
    if os.path.exists(extract_path):
        print(f"[+] Já extraído: {file_name}")
        return

    print(f"[i] Extraindo: {file_name}")
    os.makedirs(extract_path, exist_ok=True)

    try:
        mode = "r:gz" if file_name.endswith(".tar.gz") else "r:bz2"
        with tarfile.open(file_path, mode) as tar:
            tar.extractall(path=extract_path)
        print(f"[✓] Extraído em: {extract_path}")
    except Exception as e:
        print(f"[!] Erro ao extrair {file_name}: {e}")

def main():
    print(f"[i] Iniciando download e extração de {len(FILES)} arquivos...")
    for filename in FILES:
        path = download_file(filename)
        if path and (filename.endswith(".tar.gz") or filename.endswith(".tar.bz2")):
            extract_file(path)

if __name__ == "__main__":
    main()