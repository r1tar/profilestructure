# profilestructure
**データ構造を簡単にプロファイリング可能にするPython汎用モジュール**

## クイックスタート
```python
from profilestructure import ProfileStructure

db = {
    "secret_info": {
        "user": [1, 3, 5, 7, 11]
    },
    "public_info": {
        "item_a": {
            "id": 1
        },
        "item_b": {
            "id": 2
        }
    },
    "log": [...]
}
profiles = {
    "secret": ["secret_info"],
    "public": ["public_info"]
}

profiled_db = ProfileStructure(db, profiles=profiles)

profiled_db.get("secret")
"""
{
    "secret_info": {
        "user": [1, 3, 5, 7, 11]
    }
}
"""

profiled_db.get("secret", "secret_info")
"""
{
    "user": [1, 3, 5, 7, 11]
}
"""

profiled_db.get("public", "secret_info", None) # None

profiled_db.get("public", "log", None) # None
```

