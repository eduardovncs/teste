---
name: mkdocs-documentation
description: Build professional project documentation with MkDocs and Material theme. Covers site configuration, navigation, plugins, search optimization, versioning with mike, and deployment to GitHub Pages.
---

# MkDocs Documentation Skill

Build fast, beautiful project documentation with MkDocs and Material for MkDocs theme. This skill covers everything from basic setup to advanced deployment pipelines with versioning.

## Prerequisites

### Installation

```bash

# Using uv (recommended)
uv pip install mkdocs mkdocs-material

# With common plugins
pip install mkdocs mkdocs-material \
    mkdocs-minify-plugin \
    mkdocs-git-revision-date-localized-plugin \
    mkdocs-macros-plugin \
    mkdocs-glightbox

# Verify installation
mkdocs --version
```

### System Requirements

- Python 3.8 or higher
- pip or uv package manager
- Git (for git-revision plugin and mike)
- Node.js (optional, for social cards)

## Core Capabilities

### 1. Project Initialization

```bash
# Create new documentation project
mkdocs new my-project-docs
cd my-project-docs

# Project structure
# my-project-docs/
# ├── docs/
# │   └── index.md
# └── mkdocs.yml

# Or initialize in existing project
mkdir -p docs
touch docs/index.md
touch mkdocs.yml
```

### 2. Basic Configuration (mkdocs.yml)

```yaml
# mkdocs.yml - Minimal configuration
site_name: My Project Documentation
site_url: https://example.com/docs/
site_description: Comprehensive documentation for My Project
site_author: Your Name

# Repository
repo_name: username/my-project
repo_url: https://github.com/username/my-project
edit_uri: edit/main/docs/

# Theme
theme:
  name: material
  palette:
    - scheme: default
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - scheme: slate
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
  font:
    text: Roboto
    code: Roboto Mono
  features:
    - navigation.instant
    - navigation.tracking
    - navigation.tabs
    - navigation.sections
    - navigation.expand
    - navigation.top
    - search.suggest
    - search.highlight
    - content.tabs.link
    - content.code.copy
    - content.code.annotate

# Navigation
nav:
  - Home: index.md
  - Getting Started:
      - Installation: getting-started/installation.md
      - Quick Start: getting-started/quickstart.md
      - Configuration: getting-started/configuration.md
  - User Guide:
      - Overview: guide/overview.md
      - Basic Usage: guide/basic-usage.md
      - Advanced: guide/advanced.md
  - API Reference: api/reference.md
  - FAQ: faq.md
  - Changelog: changelog.md

# Plugins
plugins:
  - search:
      lang: en
      separator: '[\s\-,:!=\[\]()"/]+|(?!\b)(?=[A-Z][a-z])|\.(?!\d)|&[lg]t;'
  - minify:
      minify_html: true

# Markdown extensions
markdown_extensions:
  - abbr
  - admonition
  - attr_list
  - def_list
  - footnotes
  - md_in_html
  - toc:
      permalink: true
      toc_depth: 3
  - pymdownx.arithmatex:
      generic: true
  - pymdownx.betterem:
      smart_enable: all
  - pymdownx.caret
  - pymdownx.details
  - pymdownx.emoji:
      emoji_index: !!python/name:material.extensions.emoji.twemoji
      emoji_generator: !!python/name:material.extensions.emoji.to_svg
  - pymdownx.highlight:
      anchor_linenums: true
      line_spans: __span
      pygments_lang_class: true
  - pymdownx.inlinehilite
  - pymdownx.keys
  - pymdownx.magiclink:
      repo_url_shorthand: true
      user: username
      repo: my-project
  - pymdownx.mark
  - pymdownx.smartsymbols
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
  - pymdownx.tabbed:
      alternate_style: true
  - pymdownx.tasklist:
      custom_checkbox: true
  - pymdownx.tilde

# Extra
extra:
  social:
    - icon: fontawesome/brands/github
      link: https://github.com/username
    - icon: fontawesome/brands/twitter
      link: https://twitter.com/username
  generator: false
  version:
    provider: mike

# Copyright
copyright: Copyright &copy; 2024-2026 Your Name
```

### 3. Navigation Structure

```yaml
# mkdocs.yml - Advanced navigation
nav:
  - Home: index.md
  - Getting Started:
      - getting-started/index.md
      - Installation:
          - Linux: getting-started/install-linux.md
          - macOS: getting-started/install-macos.md
          - Windows: getting-started/install-windows.md
          - Docker: getting-started/install-docker.md
      - Quick Start: getting-started/quickstart.md
      - Configuration: getting-started/configuration.md
  - User Guide:
      - guide/index.md
      - Core Concepts:
          - Architecture: guide/architecture.md
          - Components: guide/components.md
          - Data Flow: guide/data-flow.md
      - Tutorials:
          - Basic Tutorial: guide/tutorials/basic.md
          - Advanced Tutorial: guide/tutorials/advanced.md
          - Integration: guide/tutorials/integration.md
      - Best Practices: guide/best-practices.md
  - API Reference:
      - api/index.md
      - REST API: api/rest.md
      - Python SDK: api/python-sdk.md
      - CLI Reference: api/cli.md
  - Examples:
      - examples/index.md
      - Basic Examples: examples/basic.md
      - Advanced Examples: examples/advanced.md
  - Contributing: contributing.md
  - Changelog: changelog.md
  - License: license.md
```

### 4. Material Theme Features

```yaml
# mkdocs.yml - Theme customization
theme:
  name: material
  custom_dir: docs/overrides  # Custom templates
  logo: assets/logo.png
  favicon: assets/favicon.ico
  icon:
    repo: fontawesome/brands/github
    admonition:
      note: octicons/tag-16
      warning: octicons/alert-16
      danger: octicons/zap-16
      tip: octicons/light-bulb-16
      example: octicons/beaker-16

  palette:
    # Light mode
    - media: "(prefers-color-scheme: light)"
      scheme: default
      primary: deep purple
      accent: deep purple
      toggle:
        icon: material/weather-sunny
        name: Switch to dark mode
    # Dark mode
    - media: "(prefers-color-scheme: dark)"
      scheme: slate
      primary: deep purple
      accent: deep purple
      toggle:
        icon: material/weather-night
        name: Switch to light mode

  features:
    # Navigation
    - navigation.instant
    - navigation.instant.progress
    - navigation.tracking
    - navigation.tabs
    - navigation.tabs.sticky
    - navigation.sections
    - navigation.expand
    - navigation.path
    - navigation.prune
    - navigation.indexes
    - navigation.top
    - navigation.footer
    # Table of contents
    - toc.follow
    - toc.integrate
    # Search
    - search.suggest
    - search.highlight
    - search.share
    # Header
    - header.autohide
    # Content
    - content.tabs.link
    - content.code.copy
    - content.code.select
    - content.code.annotate
    - content.tooltips
    # Announce
    - announce.dismiss
```

### 5. Admonitions and Call-outs

```markdown
<!-- docs/guide/admonitions.md -->

# Using Admonitions

MkDocs Material supports various admonition types for highlighting content.

## Note

!!! note "Important Note"
    This is a note admonition. Use it for general information
    that readers should pay attention to.

## Tip

!!! tip "Pro Tip"
    Use tips to share best practices and helpful suggestions
    that improve the reader's experience.

## Warning

!!! warning "Caution"
    Warnings alert readers to potential issues or important
    considerations they should be aware of.

## Danger

!!! danger "Critical Warning"
    Use danger for critical warnings about actions that could
    cause data loss or security issues.

## Example

!!! example "Code Example"
    ```python
    def greet(name: str) -> str:
        """Return a greeting message."""
        return f"Hello, {name}!"
    ```

## Info

!!! info "Additional Information"
    Info admonitions provide supplementary details that
    enhance understanding.

## Success

!!! success "Completed Successfully"
    Use success to indicate completed actions or
    successful outcomes.

## Question

!!! question "FAQ"
    Use question admonitions for frequently asked
    questions sections.

## Quote

!!! quote "Notable Quote"
    "Documentation is a love letter that you write to your
    future self." - Damian Conway

## Collapsible Admonitions

??? note "Click to expand"
    This admonition is collapsed by default.
    Click the title to expand it.

???+ tip "Expanded by default"
    This admonition uses `???+` to be expanded by default
    but can be collapsed by the reader.

## Inline Admonitions

!!! info inline "Inline Left"
    This appears inline on the left.

!!! tip inline end "Inline Right"
    This appears inline on the right.
```

### 6. Code Blocks with Features

```markdown
<!-- docs/guide/code-blocks.md -->

# Code Block Features

## Basic Code Block

```python
def hello_world():
    print("Hello, World!")
```

## With Title

```python title="hello.py"
def hello_world():
    print("Hello, World!")
```

## Line Numbers

```python linenums="1"
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
```

## Line Highlighting

```python hl_lines="2 4"
def process_data(data):
    validated = validate(data)  # highlighted
    transformed = transform(validated)
    return save(transformed)  # highlighted
```

## Line Number Start

```python linenums="42"
# This code block starts at line 42
def answer():
    return 42
```

## Code Annotations

```python
def calculate_area(radius: float) -> float:  # (1)!
    """Calculate the area of a circle."""
    import math  # (2)!
    return math.pi * radius ** 2  # (3)!
```

1. Type hints improve code readability
2. Import inside function for demonstration
3. Uses the formula: A = pi * r^2

## Tabbed Code Blocks

=== "Python"
    ```python
    def greet(name):
        return f"Hello, {name}!"
    ```

=== "JavaScript"
    ```javascript
    function greet(name) {
        return `Hello, ${name}!`;
    }
    ```

=== "Go"
    ```go
    func greet(name string) string {
        return fmt.Sprintf("Hello, %s!", name)
    }
    ```

=== "Rust"
    ```rust
    fn greet(name: &str) -> String {
        format!("Hello, {}!", name)
    }
    ```

## Inline Code

Use `pip install mkdocs` to install MkDocs.

The `#!python print()` function outputs text to the console.
```

### 7. Mermaid Diagrams

```markdown
<!-- docs/guide/diagrams.md -->

# Diagrams with Mermaid

## Flowchart

```mermaid
flowchart TD
    A[Start] --> B{Is it valid?}
    B -->|Yes| C[Process Data]
    B -->|No| D[Show Error]
    C --> E[Save Results]
    D --> F[Log Error]
    E --> G[End]
    F --> G
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant A as API
    participant D as Database

    U->>A: POST /api/data
    A->>A: Validate request
    A->>D: INSERT data
    D-->>A: Success
    A-->>U: 201 Created
```

## Class Diagram

```mermaid
classDiagram
    class Document {
        +String title
        +String content
        +Date created
        +save()
        +delete()
    }
    class Page {
        +int pageNumber
        +String markdown
        +render()
    }
    class Navigation {
        +List~Page~ pages
        +addPage()
        +removePage()
    }
    Document "1" --> "*" Page
    Navigation "1" --> "*" Page
```

## State Diagram

```mermaid
stateDiagram-v2
    [*] --> Draft
    Draft --> Review: Submit
    Review --> Approved: Accept
    Review --> Draft: Request Changes
    Approved --> Published: Publish
    Published --> [*]
```

## Entity Relationship

```mermaid
erDiagram
    USER ||--o{ POST : creates
    USER ||--o{ COMMENT : writes
    POST ||--|{ COMMENT : contains
    POST }|..|{ TAG : has
```

## Gantt Chart

```mermaid
gantt
    title Documentation Project
    dateFormat  YYYY-MM-DD
    section Phase 1
    Research           :a1, 2024-01-01, 7d
    Outline            :a2, after a1, 3d
    section Phase 2
    Writing            :b1, after a2, 14d
    Review             :b2, after b1, 7d
    section Phase 3
    Publishing         :c1, after b2, 3d
```
```

### 8. Plugin Configuration

```yaml
# mkdocs.yml - Comprehensive plugin setup
plugins:
  # Built-in search
  - search:
      lang: en
      separator: '[\s\-,:!=\[\]()"/]+|(?!\b)(?=[A-Z][a-z])|\.(?!\d)|&[lg]t;'
      pipeline:
        - stemmer
        - stopWordFilter
        - trimmer

  # Minification
  - minify:
      minify_html: true
      minify_js: true
      minify_css: true
      htmlmin_opts:
        remove_comments: true

  # Git revision date
  - git-revision-date-localized:
      type: timeago
      timezone: UTC
      locale: en
      fallback_to_build_date: true
      enable_creation_date: true

  # Macros for variables and templating
  - macros:
      include_dir: docs/includes
      module_name: docs/macros

  # Image lightbox
  - glightbox:
      touchNavigation: true
      loop: false
      effect: zoom
      width: 100%
      height: auto
      zoomable: true
      draggable: true

  # Social cards (requires dependencies)
  - social:
      cards_layout: default

  # Tags
  - tags:
      tags_file: tags.md

  # Blog (Material Insiders)
  # - blog:
  #     blog_dir: blog
  #     post_date_format: long
```

## Integration Examples

### Integration with Python Package

```
my-python-package/
├── src/
│   └── mypackage/
│       ├── __init__.py
│       └── core.py
├── docs/
│   ├── index.md
│   ├── getting-started/
│   ├── api/
│   └── assets/
├── tests/
├── mkdocs.yml
├── pyproject.toml
└── README.md
```

```yaml
# mkdocs.yml for Python package
site_name: MyPackage
site_url: https://username.github.io/mypackage/

theme:
  name: material
  features:
    - content.code.copy

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          paths: [src]
          options:
            docstring_style: google
            show_source: true

nav:
  - Home: index.md
  - Getting Started: getting-started.md
  - API Reference:
      - api/index.md
      - Core Module: api/core.md
  - Changelog: changelog.md
```

### Integration with Monorepo

```yaml
# mkdocs.yml for monorepo
site_name: Monorepo Documentation

nav:
  - Home: index.md
  - Packages:
      - Package A: packages/package-a/README.md
      - Package B: packages/package-b/README.md
  - Shared:
      - Contributing: CONTRIBUTING.md
      - Code of Conduct: CODE_OF_CONDUCT.md

plugins:
  - search
  - monorepo

# Reference files outside docs/
docs_dir: .
```

## Best Practices

### 1. Documentation Structure

```
docs/
├── index.md                    # Landing page
├── getting-started/
│   ├── index.md               # Section overview
│   ├── installation.md
│   ├── quickstart.md
│   └── configuration.md
├── user-guide/
│   ├── index.md
│   ├── concepts.md
│   ├── tutorials/
│   │   ├── basic.md
│   │   └── advanced.md
│   └── best-practices.md
├── api/
│   ├── index.md
│   └── reference.md
├── contributing/
│   ├── index.md
│   ├── development.md
│   └── style-guide.md
├── changelog.md
├── assets/
│   ├── images/
│   ├── stylesheets/
│   └── javascripts/
└── includes/                   # Reusable snippets
    └── abbreviations.md
```

### 2. Page Template

```markdown
---
title: Page Title
description: Brief description for SEO and social sharing
---

# Page Title

Brief introduction explaining what this page covers.

## Prerequisites

- Prerequisite 1
- Prerequisite 2

## Section 1

Content with examples...

### Subsection 1.1

More details...

## Section 2

Additional content...

## Examples

!!! example "Example Title"
    ```python
    # Code example
    pass
    ```

## See Also

- [Related Page 1](./related1.md)
- [Related Page 2](./related2.md)
```

### 3. Abbreviations

```markdown
<!-- docs/includes/abbreviations.md -->
*[HTML]: Hyper Text Markup Language
*[API]: Application Programming Interface
*[CLI]: Command Line Interface
*[CSS]: Cascading Style Sheets
*[JSON]: JavaScript Object Notation
*[YAML]: YAML Ain't Markup Language
*[REST]: Representational State Transfer
*[SDK]: Software Development Kit
*[URL]: Uniform Resource Locator
*[CI]: Continuous Integration
*[CD]: Continuous Deployment
```

```yaml
# mkdocs.yml
markdown_extensions:
  - abbr
  - pymdownx.snippets:
      auto_append:
        - docs/includes/abbreviations.md
```

### 4. SEO Optimization

```yaml
# mkdocs.yml
plugins:
  - search
  - social
  - meta

extra:
  social:
    - icon: fontawesome/brands/twitter
      link: https://twitter.com/username
  analytics:
    provider: google
    property: G-XXXXXXXXXX
```

### 5. Performance Optimization

```yaml
# mkdocs.yml - Performance settings
theme:
  features:
    - navigation.instant  # Preload pages
    - navigation.prune    # Reduce navigation size

plugins:
  - minify:
      minify_html: true
      minify_js: true
      minify_css: true
  - optimize:
      enabled: true
```

## Troubleshooting

### Common Issues

#### Build Fails with "Page not in nav"

```yaml
# mkdocs.yml - Allow pages not in nav
validation:
  nav:
    omitted_files: info
    not_found: warn
    absolute_links: info
```

#### Mermaid Diagrams Not Rendering

```yaml
# Ensure superfences is configured correctly
markdown_extensions:
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
```

#### Search Not Working

```yaml
# Check search configuration
plugins:
  - search:
      lang: en
      prebuild_index: true  # Build search index at build time
```

#### Social Cards Generation Fails

```bash
# Install required dependencies
uv add pillow cairosvg
```

### Debug Mode

```bash
# Verbose build output
mkdocs build --verbose

# Strict mode catches warnings as errors
mkdocs build --strict
```

*Build beautiful, searchable documentation sites with MkDocs and deploy them anywhere.*