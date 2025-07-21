from __future__ import annotations

from collections import defaultdict
from .exceptions import UnknownProfileError

class ProfileStructure:
    def __init__(self, structure: dict|list, profiles: dict, default=None):
        self._structure = self._profile(structure, profiles, default)

    def _profile(self, structure: dict, profiles: dict, default) -> dict:
        """
        プロファイルをkeyとするdictを返す
        ex) {"p1": ..., "p2": ...}
        """
        if isinstance(structure, dict):
            return {p: structure.get(k, default) for p, k in profiles.items()}
        elif isinstance(structure, list):
            profiles_key = defaultdict(list)
            [profiles_key[p].append(structure[i]) for p, i in profiles.items()]
            return dict(profiles_key)
        else:
            raise TypeError("Structure must be a dict or list")

    def get(self, profile, key=None, default=None):
        """
        Get the value for a specific profile and key.
        """
        # TODO: listにも対応させるためkeyを再度命名
        # keyがNoneならプロファイルの値を返す
        if key is None:
            return self._structure.get(profile, default)
        
        # そうでなければプロファイルに含まれるkeyの値を返す
        return self._structure.get(profile, {}).get(key, default)

    def set(self, profile, value) -> None:
        """
        Set the value for a specific profile.
        """
        # {"p1": {"id": 1}}ならinstance.get("p1")をして["id"] = 1をすれば変更可能
        if not self.has(profile):
            raise UnknownProfileError(f"Profile '{profile}' does not exist.")
        self._structure[profile] = value
    
    def has(self, profile, key=None) -> bool:
        """
        プロファイルが存在するか、またはプロファイル内に特定のキーが存在するかを返す。
        """
        if key:
            return key in self._structure.get(profile, {})
        else:
            return profile in self._structure
        
    def move_profile(self, key, old_profile, new_profile, strict: bool = False) -> None:
        """
        Move a key from one profile to another.
        """
        # プロファイル変更対象が存在しないのでKeyErrorを送出
        if not self.has(old_profile, key):
            raise KeyError(f"Key '{key}' does not exist in profile '{old_profile}'.")

        # 新しいプロファイルが存在しない場合、strictがTrueならUnknownProfileErrorを送出
        # そうでなければ新しいプロファイルを作成
        if not self.has(new_profile):
            if strict:
                raise UnknownProfileError(f"Profile '{new_profile}' does not exist.")
            self._structure[new_profile] = {}

        self._structure[new_profile][key] = self._structure[old_profile].pop(key)

    def create_profile(self, profile, value=None, strict: bool = False) -> None:
        """
        Create a new profile.
        """
        if self.has(profile):
            if strict:
                raise UnknownProfileError(f"Profile '{profile}' already exists.")
            return
        self._structure[profile] = value

    def delete_profile(self, profile, strict: bool = False) -> None:
        """
        Delete a profile.
        """
        if not self.has(profile):
            if strict:
                raise UnknownProfileError(f"Profile '{profile}' does not exist.")
            return
        del self._structure[profile]

    def change_profile_name(self, profile, name, overwrite: bool = False) -> None:
        """
        Change the name of a profile.
        """
        if not self.has(profile):
            raise UnknownProfileError(f"Profile '{profile}' does not exist.")

        if self.has(name):
            if not overwrite:
                raise UnknownProfileError(f"Profile '{name}' already exists.")
            return
        self._structure[name] = self._structure.pop(profile)
    
    def dict(self) -> dict:
        """
        Return the structure as a dictionary.
        """
        return # {v for v in self._structure.values()}