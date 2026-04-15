import os

def generate():
    cpp_dir = "app/src/main/cpp"
    os.makedirs(cpp_dir, exist_ok=True)
    
    cmake_content = """cmake_minimum_required(VERSION 3.18.1)
project("watermarker")

add_library(watermarker SHARED watermarker.cpp)

find_library(log-lib log)
target_link_libraries(watermarker ${log-lib} jnigraphics)
"""
    with open(f"{cpp_dir}/CMakeLists.txt", "w") as f:
        f.write(cmake_content)
    print("✅ 4-1 Generated CMakeLists.txt")

if __name__ == "__main__":
    generate()
