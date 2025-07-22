from __future__ import annotations

from collections import defaultdict
from .exceptions import UnknownProfileError, UnsupportedTypeError

class ProfileStructure:
    def __init__(self, structure: dict|list, profiles: dict[str, list], default=None):
        self._profiles = self._profile(structure, profiles, default)

    def _profile(self, structure: dict, profiles: dict[str, list], default) -> dict:
        """
        プロファイルをkeyとするdictを返す
        ex) {"p1": {...} "p2": {...}}

        structureがlistの場合、それぞれのprofileの値であるリストの内容はstructureのインデックスとして解釈される。
        """
        # TODO: 複数のプロファイルが同じkeyを指定した場合の挙動をどうするかを決定する
        # 同じ値を共有するように実装したいが方法が不明
        # 現在はそれぞれに値を代入しているので変更があった際に同期されない
        # 

        # HACK: コードの大部分が重複している
        if isinstance(structure, dict):
            profiles_key = defaultdict(dict)
            for p, keys in profiles.items():
                for k in keys:
                    if p not in profiles_key:
                        self.create_profile(p, {}, strict=True)
                    profiles_key[p][k] = structure.get(k, default)
            return dict(profiles_key)
        elif isinstance(structure, list):
             profiles_key = defaultdict(dict)
             for p, indexes in profiles.items():
                for i in indexes:
                    if p not in profiles_key:
                        self.create_profile(p, {}, strict=True)
                    profiles_key[p][k] = structure[i] if 0 <= i < len(structure) else default
             return dict(profiles_key)
        else:
            raise UnsupportedTypeError("Structure must be a dict or list")

    def get(self, profile, key=None, default=None):
        """
        Get the value for a specific profile and key.
        """
        # keyがNoneならプロファイルの値を返す
        if key is None:
            return self._profiles.get(profile, default)
        
        # そうでなければプロファイルに含まれるkeyの値を返す
        return self._profiles.get(profile, {}).get(key, default)
    
    def has(self, profile, key=None) -> bool:
        """
        プロファイルが存在するか、またはプロファイル内に特定のキーが存在するかを返す。
        """
        if key:
            return key in self._profiles.get(profile, {})
        else:
            return profile in self._profiles
        
    def set(self, profile, value, key=None, strict: bool = False) -> None:
        """
        Set the value for a specific profile.
        """
        if not self.has(profile, key):
            if strict:
                raise UnknownProfileError(f"Profile '{profile}' or key '{key}' does not exist.")
            self.create_profile(profile, {}, strict=True)
        if key:
            # keyの内容を更新
            self._profiles[profile][key] = value
        else:
            # profileの内容を上書き
            # valueがdictでないと機能しなくなるのでUnsupportedTypeErrorを送出
            if not isinstance(value, dict):
                raise UnsupportedTypeError("Value must be a dict when key is None")
            self._profiles[profile] = value

    def create_profile(self, profile, value=None, strict: bool = False) -> None:
        """
        Create a new profile.
        """
        if self.has(profile):
            if strict:
                raise UnknownProfileError(f"Profile '{profile}' already exists.")
            return
        self._profiles[profile] = value

    def delete_profile(self, profile, strict: bool = False) -> None:
        """
        Delete a profile.
        """
        if not self.has(profile):
            if strict:
                raise UnknownProfileError(f"Profile '{profile}' does not exist.")
            return
        del self._profiles[profile]

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
            self.create_profile(new_profile, {}, strict=True)

        self._profiles[new_profile][key] = self._profiles[old_profile].pop(key)

    def change_profile_name(self, profile, name, overwrite: bool = False) -> None:
        """
        Change the name of a profile.
        """
        if not self.has(profile):
            raise UnknownProfileError(f"Profile '{profile}' does not exist.")

        if self.has(name):
            if not overwrite:
                raise UnknownProfileError(f"Profile '{name}' already exists.")

        self._profiles[name] = self._profiles.pop(profile)
    
    def as_dict(self, allow_duplicates: bool = True) -> dict:
        """
        Return the structure as a dictionary.
        """
        keys_content = {}
        for profile_content in list(self._profiles.values()):
            for k, v in profile_content.items():
                if not allow_duplicates and k in keys_content:
                    raise ValueError(f"Duplicate key '{k}' found in profiles.")
                keys_content[k] = v
        return keys_content
    
    def as_list(self, default=None, allow_duplicates: bool = True) -> dict:
        """
        Return the structure as a list.
        """
        as_dict = self.as_dict(allow_duplicates)
        sorted_dict_keys = sorted(as_dict.keys())
        return [as_dict[i] if i in as_dict else default for i in sorted_dict_keys]