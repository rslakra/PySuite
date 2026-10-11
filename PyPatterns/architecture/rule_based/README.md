# Rule-Based Pattern

## Intent

Encode business logic as a set of **declarative rules** evaluated against a shared **fact base**. A rules engine matches conditions and fires actions, keeping policy separate from application flow.

This demo applies free-shipping and member-discount rules to a shopping-cart fact dictionary.

## Class Diagram

```mermaid
classDiagram
    class RulesEngine {
        +rules: list
        +fired: list
        +add(name, action)
        +run(facts) dict
    }
    class Rule {
        <<callable>>
        +evaluate(facts) bool
    }
    class FactBase {
        +cart_total: float
        +member: bool
        +discount: float
    }
    RulesEngine o-- Rule
    RulesEngine --> FactBase : mutates
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant App as Application
    participant E as RulesEngine
    participant F as Facts

    App->>F: load cart_total, member
    App->>E: run(facts)
    E->>E: evaluate free-shipping
    E->>F: set free_shipping=true
    E->>E: evaluate member-discount
    E->>F: set discount=0.10
    E-->>App: updated facts
```

## Flowchart

```mermaid
flowchart TD
    A[Load facts into working memory] --> B[Select next rule]
    B --> C{Condition matches?}
    C -->|Yes| D[Execute action / mutate facts]
    D --> E[Mark rule fired]
    E --> F{More rules changed facts?}
    F -->|Yes| B
    F -->|No| G[Return final facts]
    C -->|No| H{More rules?}
    H -->|Yes| B
    H -->|No| G
```

## Run Instructions

```bash
cd PyPatterns
python3 architecture/rule_based/demo.py
```

Expected output shows both rules firing and final facts with discount and free shipping applied.

## Pros / Cons

| Pros | Cons |
| ---- | ---- |
| Business rules change without redeploying code | Rule interaction and ordering can surprise teams |
| Non-developers can author rules (with tooling) | Debugging forward-chaining cycles is hard |
| Centralizes policy — fewer scattered conditionals | Performance tuning needed for large rule sets |
| Fits pricing, eligibility, routing, fraud checks | Overkill for trivial one-off conditions |

## Distributed Environments

Rule engines power **policy-heavy domains**:

- **Drools**, **Easy Rules**, **Open Policy Agent (OPA)** for authorization and admission control.
- **AWS EventBridge** rules route events by pattern matching.
- **Fraud detection** and **credit scoring** pipelines evaluate fact streams.
- **Kubernetes admission webhooks** and **Istio** policies enforce cluster rules.

OPA/Rego is popular for **policy-as-code** in GitOps workflows; Drools suits complex forward/backward chaining in JVM ecosystems.

## References

- [Business rules engine — Wikipedia](https://en.wikipedia.org/wiki/Business_rules_engine)
- [Forward chaining — Wikipedia](https://en.wikipedia.org/wiki/Forward_chaining)
- [List of software architecture styles and patterns — Wikipedia](https://en.wikipedia.org/wiki/List_of_software_architecture_styles_and_patterns)
