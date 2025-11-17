#!/usr/bin/env python3
"""Script to auto-fix common linting issues."""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def fix_typing_imports(content: str) -> str:
    """Replace typing imports with modern syntax."""
    # Replace Dict -> dict, List -> list, Tuple -> tuple
    content = re.sub(r"\bDict\[", "dict[", content)
    content = re.sub(r"\bList\[", "list[", content)
    content = re.sub(r"\bTuple\[", "tuple[", content)
    
    # Replace Optional[X] -> X | None
    content = re.sub(r"Optional\[([^\]]+)\]", r"\1 | None", content)
    
    # Remove typing imports that are no longer needed
    lines = content.split("\n")
    new_lines = []
    for line in lines:
        # Remove Dict, List, Tuple, Optional from typing imports if they're the only ones
        if "from typing import" in line:
            imports = re.findall(r"from typing import (.+)", line)
            if imports:
                import_list = [i.strip() for i in imports[0].split(",")]
                # Keep only non-deprecated imports
                kept = [i for i in import_list if i not in ["Dict", "List", "Tuple", "Optional"]]
                if kept:
                    new_lines.append(f"from typing import {', '.join(kept)}")
                elif "Any" in import_list or "Iterable" in import_list or "Iterator" in import_list or "Literal" in import_list:
                    new_lines.append(line)
                else:
                    # Remove the line if all imports are deprecated
                    continue
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    return "\n".join(new_lines)


def fix_file_mode_args(content: str) -> str:
    """Remove unnecessary mode arguments from open()."""
    content = re.sub(r'open\(([^,]+),\s*"r",\s*encoding=', r'open(\1, encoding=', content)
    content = re.sub(r'open\(([^,]+),\s*"w",\s*encoding=', r'open(\1, encoding=', content)
    return content


def fix_collections_abc_imports(content: str) -> str:
    """Fix imports to use collections.abc."""
    content = re.sub(
        r"from typing import.*\b(Iterable|Iterator)\b",
        lambda m: m.group(0).replace("typing", "collections.abc"),
        content
    )
    return content


def process_file(file_path: Path) -> bool:
    """Process a single file and fix linting issues."""
    try:
        content = file_path.read_text(encoding="utf-8")
        original = content
        
        # Apply fixes
        content = fix_typing_imports(content)
        content = fix_file_mode_args(content)
        content = fix_collections_abc_imports(content)
        
        if content != original:
            file_path.write_text(content, encoding="utf-8")
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Main entry point."""
    backend_src = REPO_ROOT / "backend" / "src"
    ai_dir = REPO_ROOT / "ai"
    
    files_modified = 0
    
    # Process backend/src
    if backend_src.exists():
        for py_file in backend_src.rglob("*.py"):
            if process_file(py_file):
                files_modified += 1
                print(f"Fixed: {py_file.relative_to(REPO_ROOT)}")
    
    # Process ai/
    if ai_dir.exists():
        for py_file in ai_dir.rglob("*.py"):
            if process_file(py_file):
                files_modified += 1
                print(f"Fixed: {py_file.relative_to(REPO_ROOT)}")
    
    print(f"\nModified {files_modified} files.")
    print("Note: Some issues may require manual fixes. Run ruff check --fix for remaining issues.")


if __name__ == "__main__":
    main()

