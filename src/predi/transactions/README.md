```mermaid
erDiagram
    PrediTransaction ||--o{ ORDER : places
    ORDER ||--|{ LINE-ITEM : contains
    PrediTransaction }|..|{ DELIVERY-ADDRESS : uses
```