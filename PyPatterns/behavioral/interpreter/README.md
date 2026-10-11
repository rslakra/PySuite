# Interpreter

## Intent

Given a language, define a representation for its grammar along with an interpreter that uses the representation to interpret sentences in the language.

This demo evaluates a simple arithmetic expression tree for **5 + 3**.

## Run

```bash
python3 behavioral/interpreter/demo.py
```

## Class Diagram

```mermaid
classDiagram
    class Expression {
        <<abstract>>
        +interpret() int
    }
    class Number {
        -int _value
        +interpret() int
    }
    class Add {
        -Expression _left
        -Expression _right
        +interpret() int
    }
    class Subtract {
        -Expression _left
        -Expression _right
        +interpret() int
    }
    Expression <|-- Number
    Expression <|-- Add
    Expression <|-- Subtract
    Add --> Expression : left, right
    Subtract --> Expression : left, right
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant Client
    participant Add as Add(5, 3)
    participant Left as Number(5)
    participant Right as Number(3)

    Client->>Add: interpret()
    Add->>Left: interpret()
    Left-->>Add: 5
    Add->>Right: interpret()
    Right-->>Add: 3
    Add-->>Client: 8
```

## Flowchart

```mermaid
flowchart TD
    A[Build expression tree] --> B[Call interpret on root]
    B --> C{Node type?}
    C -->|Number| D[Return literal value]
    C -->|Add| E[Interpret left subtree]
    E --> F[Interpret right subtree]
    F --> G[Return sum]
    C -->|Subtract| H[Interpret left subtree]
    H --> I[Interpret right subtree]
    I --> J[Return difference]
```

## Pros and Cons

| Pros | Cons |
| ---- | ---- |
| Easy to implement simple grammars | Complex grammars become hard to maintain |
| Open/Closed — add new expression types easily | Performance can suffer vs compiled parsers |
| Each grammar rule is a class | Debugging nested trees is non-trivial |

## Distributed Environments

Interpreter pattern appears in **rule engines** and **DSL evaluation** across services:

- **Policy engines** (OPA, AWS IAM policies) interpret declarative rules at runtime.
- **Workflow DSLs** (Temporal, Airflow DAG definitions) parse and execute domain-specific instructions.
- **Query languages** (GraphQL resolvers, SQL planners) interpret AST nodes into execution plans.

In distributed setups, prefer compiling hot-path expressions to bytecode or caching parse trees. Ship grammar definitions as versioned schemas so all nodes interpret consistently.

## References

- [Interpreter — Refactoring.Guru](https://refactoring.guru/design-patterns/interpreter)
- [Interpreter pattern — Wikipedia](https://en.wikipedia.org/wiki/Interpreter_pattern)
