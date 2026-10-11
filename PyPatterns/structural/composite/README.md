# Composite Pattern

## Intent

Compose objects into tree structures to represent part-whole hierarchies. Composite lets clients treat individual objects and compositions uniformly.

This demo models a **file system**: **File** (leaf) and **Directory** (composite) both implement **FileSystemNode**, so size and display work the same whether you query a single file or an entire project tree.

## Class Diagram

```mermaid
classDiagram
    class FileSystemNode {
        <<interface>>
        +name: str
        +size() int
        +display(indent) str
    }
    class File {
        +bytes_size: int
        +size() int
        +display(indent) str
    }
    class Directory {
        -_children: list
        +add(node) void
        +size() int
        +display(indent) str
    }
    FileSystemNode <|.. File
    FileSystemNode <|.. Directory
    Directory o-- FileSystemNode : contains *
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant Client
    participant Root as Directory
    participant Src as Directory
    participant File as File

    Client->>Root: display()
    Root->>Root: size() — sum children
    Root->>Src: display(indent+1)
    Src->>File: display(indent+2)
    File-->>Src: "main.py (1200 B)"
    Src-->>Root: subtree string
    Root-->>Client: full tree
```

## Flowchart

```mermaid
flowchart TD
    A[Client calls node.size or display] --> B{Node type?}
    B -->|File| C[Return bytes_size]
    B -->|Directory| D[Iterate children]
    D --> E[Recursively sum child.size]
    E --> F[Return aggregate]
    C --> G[Uniform result to client]
    F --> G
```

## Run Instructions

```bash
cd PyPatterns
python3 structural/composite/demo.py
```

Prints an indented directory tree and total project size computed recursively.

## Pros / Cons

| Pros | Cons |
| ---- | ---- |
| Uniform API for leaves and composites | Hard to restrict which operations belong on leaves vs composites |
| Easy to add new component types | Can make type safety weaker (everything is `FileSystemNode`) |
| Simplifies client code — no special cases for folders | Deep trees can make debugging recursive calls harder |

## Distributed Environments

Composite structures appear in **distributed hierarchies**:

- **Kubernetes resources** — Deployments contain ReplicaSets contain Pods; `kubectl` treats the tree uniformly for apply/delete.
- **Org / permission trees** — IAM policies inherit through OU → account → resource group nesting.
- **Configuration bundles** — Helm charts, Terraform modules, and Consul key prefixes compose nested settings.

A distributed file catalog (S3 prefixes, HDFS paths) often exposes a composite API so clients list `size()` or `delete()` on a "folder" without knowing whether the backend stores real directories or flat keys with `/` delimiters.

## References

- [Composite — Refactoring.Guru](https://refactoring.guru/design-patterns/composite)
- [Composite pattern — Wikipedia](https://en.wikipedia.org/wiki/Composite_pattern)
