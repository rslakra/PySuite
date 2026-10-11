# Memento

## Intent

Without violating encapsulation, capture and externalize an object's internal state so that the object can be restored to this state later.

This demo models a **text editor** that saves snapshots to a history stack and restores previous content.

## Run

```bash
python3 behavioral/memento/demo.py
```

## Class Diagram

```mermaid
classDiagram
    class EditorMemento {
        +str content
    }
    class TextEditor {
        -str _content
        +write(text)
        +content() str
        +save() EditorMemento
        +restore(memento)
    }
    class History {
        -list~EditorMemento~ _snapshots
        +push(memento)
        +pop() EditorMemento
    }
    TextEditor ..> EditorMemento : creates
    History o-- EditorMemento
    TextEditor ..> History : used by client
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant Client
    participant Editor as TextEditor
    participant History

    Client->>Editor: write("Hello")
    Client->>Editor: save()
    Editor-->>Client: EditorMemento
    Client->>History: push(memento)
    Client->>Editor: write(", World!")
    Client->>History: pop()
    History-->>Client: memento
    Client->>Editor: restore(memento)
```

## Flowchart

```mermaid
flowchart TD
    A[Edit document] --> B{Save requested?}
    B -->|Yes| C[Create memento from current state]
    C --> D[Push memento onto history]
    D --> A
    B -->|No| E{Restore requested?}
    E -->|No| A
    E -->|Yes| F{History empty?}
    F -->|Yes| G[No snapshot available]
    F -->|No| H[Pop memento and restore editor]
    H --> A
```

## Pros and Cons

| Pros | Cons |
| ---- | ---- |
| Preserves encapsulation of originator | Large state snapshots consume memory |
| Simple undo/redo implementation | Caretaker must manage memento lifecycle |
| Originators control what gets saved | Deep copies can be expensive |

## Distributed Environments

Memento concepts underpin **snapshots**, **backups**, and **versioning**:

- **Database snapshots** (PostgreSQL PITR, DynamoDB backups) capture consistent state for restore.
- **Event sourcing** stores state transitions; snapshots accelerate replay.
- **Kubernetes etcd** and **Raft log compaction** use snapshotting to bound storage growth.

In distributed systems, mementos must be **consistent across replicas**. Use vector clocks or CRDTs when merging concurrent edits. Store snapshots in durable object storage (S3, GCS) with retention policies.

## References

- [Memento — Refactoring.Guru](https://refactoring.guru/design-patterns/memento)
- [Memento pattern — Wikipedia](https://en.wikipedia.org/wiki/Memento_pattern)
