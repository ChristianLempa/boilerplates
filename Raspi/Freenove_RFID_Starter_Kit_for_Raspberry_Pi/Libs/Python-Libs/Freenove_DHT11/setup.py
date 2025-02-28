# Filename    : setup.py
# Description : Compile DHT11 to generate the so file and copy it to the specified folder.
#               Used for Python.
#				Program transplantation by Freenove.
# Author      : Zhentao Lin
# modification: 2024/7/29
import os
import subprocess  
import shutil  
  
def compile_dht_module():  
    try:  
        subprocess.run([  
            'gcc', '-fPIC', '-c', 'DHT.c', '-o', 'DHT.o', '-lwiringPi'  
        ], check=True)  
    except subprocess.CalledProcessError as e:  
        print(f"Failed to compile DHT.c to DHT.o: {e}")  
        return False  
    try:  
        subprocess.run([  
            'gcc', '-shared', '-fPIC', 'DHT.o', '-o', 'libdht.so', '-lwiringPi'  
        ], check=True)  
    except subprocess.CalledProcessError as e:  
        print(f"Failed to compile DHT.o to libdht.so: {e}")  
        return False  
    try:  
        shutil.copy('DHT.h', '/usr/include/DHT.h')  
    except IOError as e:  
        print(f"Failed to copy DHT.h to /usr/include/{e}")  
        return False  
    try:  
        shutil.copy('libdht.so', '/usr/lib/libdht.so')  
    except IOError as e:  
        print(f"Failed to copy libdht.so to /usr/lib/{e}")  
        return False  
    try:  
        subprocess.run(['sudo', 'ldconfig'], check=True)  
    except subprocess.CalledProcessError as e:  
        print(f"Failed to run ldconfig: {e}")  
        return False  
    return True  
  
if __name__ == "__main__":  
    os.system("cd /usr/bin && sudo rm python && sudo ln -s python3 python")
    os.system("sudo apt-get update")
    os.system("git clone https://github.com/WiringPi/WiringPi")
    os.system("cd WiringPi && sudo ./build")


    if compile_dht_module():  
        print("build completed!")  
    else:  
        print("Build failed.")