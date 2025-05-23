# Coding Standards for IntelliSubs

To ensure code quality, readability, and maintainability, all contributions to IntelliSubs should adhere to the following coding standards.

## 1. Code Formatting

*   **PEP 8:** All Python code must follow the [PEP 8 -- Style Guide for Python Code](https://www.python.org/dev/peps/pep-0008/).
*   **Formatter - Black:** We use [Black, the uncompromising Python code formatter](https://github.com/psf/black) to ensure uniform code style.
    *   **Configuration:** Black is run with its default settings (e.g., line length 88 characters).
    *   **Usage:** Before committing code, format your changes using Black:
        ```bash
        pip install black  # If not already installed
        black .
        ```
    *   **IDE Integration:** Configure your IDE (e.g., VS Code) to format on save using Black.
        *   In VS Code, set `editor.formatOnSave` to `true` and `python.formatting.provider` to `black`.
*   **Line Length:** Maximum 88 characters per line (as enforced by Black). Docstrings or comments can be longer if necessary for clarity, wrapped appropriately.
*   **Imports:**
    *   Imports should be grouped in the following order:
        1.  Standard library imports (e.g., `os`, `sys`).
        2.  Related third-party imports (e.g., `customtkinter`, `openai`, `faster_whisper`).
        3.  Local application/library specific imports (e.g., `from intellisubs.core import ...`).
    *   Separate each group with a blank line.
    *   Within each group, imports should be sorted alphabetically.
    *   Use absolute imports where possible (e.g., `from intellisubs.utils.config_manager import ConfigManager` instead of `from .utils.config_manager import ConfigManager` if it makes sense for clarity from a higher level). Relative imports are fine within the same sub-package.
    *   Tools like `isort` can help manage import sorting (Black is also compatible with `isort`).

## 2. Linting

*   **Flake8:** We use [Flake8](https://flake8.pycqa.org/en/latest/) for linting to catch common errors and style issues not covered by Black.
    *   **Configuration:** A `.flake8` configuration file might be present in the project root to customize rules (e.g., extend max line length for Flake8 to match Black, ignore specific warnings if necessary after discussion).
        ```ini
        [flake8]
        max-line-length = 88
        extend-ignore = E203  ; Whitespace before ':' (often conflicts with Black)
        # Add other ignores as needed, e.g.:
        # ignore = W503 ; line break before binary operator (Black prefers this)
        ```
    *   **Usage:**
        ```bash
        pip install flake8  # If not already installed
        flake8 .
        ```
*   **Pylance (VS Code):** If using VS Code, the Pylance extension provides excellent real-time linting and type checking.

## 3. Naming Conventions

*   **Modules:** `lowercase_with_underscores.py` (e.g., `config_manager.py`).
*   **Packages:** `short_lowercase_names` (e.g., `core`, `utils`).
*   **Classes:** `CapWords` (PascalCase) (e.g., `WorkflowManager`, `SubtitleFormatter`).
*   **Methods and Functions:** `lowercase_with_underscores` (e.g., `load_config`, `process_audio_to_subtitle`).
*   **Variables:** `lowercase_with_underscores` (e.g., `api_key`, `subtitle_entries`).
*   **Constants:** `ALL_CAPS_WITH_UNDERSCORES` (e.g., `DEFAULT_MODEL_NAME`, `MAX_RETRIES`).
*   **Private/Internal:** Prefix with a single underscore `_` (e.g., `_internal_helper_function`, `self._internal_state`). For name mangling (rarely needed), use double underscore `__`.

## 4. Docstrings and Commenting

*   **Docstrings (PEP 257):** All public modules, functions, classes, and methods must have docstrings.
    *   **Format:** Use [Google Python Style Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) or [NumPy/SciPy docstring standard](https://numpydoc.readthedocs.io/en/latest/format.html) (Sphinx can parse both well). Google style is often preferred for its readability.
        *   **Example (Google Style):**
            ```python
            def my_function(arg1: str, arg2: int = 0) -> bool:
                """Does something interesting.

                This is a more detailed explanation of what the function
                does and any important considerations for its use.

                Args:
                    arg1 (str): The first argument, a string.
                    arg2 (int, optional): The second argument, an integer.
                                          Defaults to 0.

                Returns:
                    bool: True if successful, False otherwise.

                Raises:
                    ValueError: If arg1 is an empty string.
                """
                if not arg1:
                    raise ValueError("arg1 cannot be empty")
                # ... function logic ...
                return True
            ```
    *   **First line:** A concise summary of the object's purpose, fitting on one line.
    *   **Multi-line docstrings:** Should have a blank line after the summary, followed by a more detailed explanation.
*   **Comments:**
    *   Use comments to explain non-obvious parts of the code.
    *   Write comments as complete sentences.
    *   Keep comments up-to-date with code changes.
    *   Inline comments should be used sparingly: `# This is an inline comment explaining a tricky part.`
    *   Use `# TODO:` or `# FIXME:` comments to mark areas that need future attention. Include your name/initials and date if helpful: `# TODO(YourName, YYYY-MM-DD): Refactor this section.`

## 5. Type Hinting (PEP 484)

*   Use type hints for function arguments, return values, and variables where it improves clarity and allows for static analysis.
*   This is crucial for larger projects to catch type-related errors early.
*   Pylance in VS Code leverages type hints heavily for autocompletion and error checking.
    ```python
    from typing import List, Dict, Optional

    def process_data(data: List[Dict[str, int]], config_path: Optional[str] = None) -> bool:
        # ...
        pass
    ```

## 6. Git Commit Message Conventions

*   Follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification. This helps in generating changelogs and makes commit history more readable.
*   **Format:**
    ```
    <type>[optional scope]: <description>

    [optional body]

    [optional footer(s)]
    ```
*   **Common types:**
    *   `feat`: A new feature.
    *   `fix`: A bug fix.
    *   `docs`: Documentation only changes.
    *   `style`: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc).
    *   `refactor`: A code change that neither fixes a bug nor adds a feature.
    *   `perf`: A code change that improves performance.
    *   `test`: Adding missing tests or correcting existing tests.
    *   `build`: Changes that affect the build system or external dependencies (example scopes: gulp, broccoli, npm).
    *   `ci`: Changes to our CI configuration files and scripts (example scopes: Travis, Circle, BrowserStack, SauceLabs).
    *   `chore`: Other changes that don't modify src or test files.
*   **Example:**
    ```
    feat(ui): Add dark mode toggle button to settings panel

    Implements a new button in the settings panel that allows users
    to switch between light, dark, and system appearance modes.
    The application theme is updated dynamically.

    Closes #123
    ```

## 7. General Principles

*   **DRY (Don't Repeat Yourself):** Avoid duplicating code. Use functions and classes to encapsulate reusable logic.
*   **KISS (Keep It Simple, Stupid):** Prefer simple, straightforward solutions over overly complex ones.
*   **Readability Counts:** Write code that is easy for others (and your future self) to understand.
*   **Test Your Code:** Write unit tests for new functionality and bug fixes. (See [Testing Strategy](../DEVELOPMENT.md#9-测试策略概要)).

## 8. File Structure and Length

*   **Modularity:** Aim for small, focused Python files (modules) that handle a specific piece of functionality. This improves readability, testability, and maintainability.
*   **File Length Guidelines (for AI Agent-assisted Development):**
    *   This software is designed with AI Agent (e.g., Roo Code) assisted development in mind. Based on current Large Language Model (LLM) capabilities and context window limitations when editing code:
        *   **Recommended Maximum:** Strive to keep Python files **under 500 lines** of code (LoC).
        *   **Caution Zone:** When a file approaches **700 LoC**, proactively consider refactoring and splitting it into smaller, more manageable modules.
        *   **Hard Limit (Refactor Required):** Files exceeding **1000 LoC** must be refactored. Large files can significantly degrade the performance and accuracy of AI code editing tools and increase the likelihood of errors during automated changes.
    *   Regularly review larger files and identify opportunities for decomposition. This not only aids AI tools but also generally leads to better software design.
---

Adherence to these standards will help maintain a high-quality codebase for IntelliSubs. Linters and formatters will be set up to automate checks where possible.