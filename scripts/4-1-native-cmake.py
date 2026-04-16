import os

def generate():
    # Ensure the directory exists
    cmake_dir = "app/src/main/cpp"
    os.makedirs(cmake_dir, exist_ok=True)

    cmake_content = """cmake_minimum_required(VERSION 3.22.1)

project("watermarker")

add_library(
        watermarker
        SHARED
        native-engine.cpp)

find_library(
        log-lib
        log)

# Add the jnigraphics library for bitmap manipulation
find_library(
        jnigraphics-lib
        jnigraphics)

target_link_libraries(
        watermarker
        ${log-lib}
        ${jnigraphics-lib})
"""
    # Write the file to the exact path Gradle is looking for
    with open(f"{cmake_dir}/CMakeLists.txt", "w") as f:
        f.write(cmake_content)
    print("✅ 4-1 Generated CMakeLists.txt (Native Build Configuration)")

if __name__ == "__main__":
    generate()
