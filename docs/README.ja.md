# profilestructure
**データ構造を簡単にプロファイリング可能にするPython汎用モジュール**

## クイックスタート
```python
from profilestructure import ProfileStructure as ProStruct

db = {
    "secret_info": {
        "item_a": {
            "id": 1
        }
    },
    "public_info": {
        "item_b": {
            "id": 2
        }
    },
    "log": [...]
}

profiled_db = ProStruct(db, profiles={"secret": ["secret_info"], "public": ["public_info"]})

profiled_db.get("secret")
"""
{
    "secret"_info": {...}
}
"""

profiled_db.get("secret", "secret_info")
"""
{
    "item_a": {
        "id": 1
    }
}
"""

profiled_db.get("public", "secret_info", None) # None

profiled_db.get("public", "log", None) # None
```

