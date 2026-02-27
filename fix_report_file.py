
import os
import sys

def fix_file():
    target_file = "report_ui.py"
    if not os.path.exists(target_file):
        print(f"File {target_file} not found.")
        return

    with open(target_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    start_cut_index = -1
    end_cut_index = -1
    
    # Identify the unique marker line in the NEW code (the commented out QMessageBox)
    marker_content = '# QMessageBox.critical(self, "导出失败", f"生成 PDF 时发生错误：\\n{str(e)}")'
    
    for idx, line in enumerate(lines):
        if marker_content in line:
            start_cut_index = idx
            break
            
    # Identify the start of the main block at the end of the file
    main_block_marker = 'if __name__ == "__main__":'
    for idx in range(len(lines) - 1, -1, -1):
        if main_block_marker in lines[idx]:
            end_cut_index = idx
            break

    if start_cut_index == -1:
        print("Could not find the start cut marker (commented QMessageBox). File might differ from expectation.")
        return
        
    if end_cut_index == -1:
        print("Could not find the end cut marker (if __name__ == '__main__':).")
        return

    if start_cut_index >= end_cut_index:
        print(f"Indices invalid: start={start_cut_index}, end={end_cut_index}. The duplicate might already be gone or file is confused.")
        return

    print(f"Cutting from line {start_cut_index + 1} to {end_cut_index - 1}")
    
    # Keep lines up to start_cut_index (inclusive of the marker line)
    # Then skip everything until end_cut_index
    new_lines = lines[:start_cut_index+1]
    new_lines.append("\n\n") # Add some spacing
    new_lines.extend(lines[end_cut_index:])
    
    with open(target_file, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
        
    print("File fixed successfully.")

if __name__ == "__main__":
    fix_file()
