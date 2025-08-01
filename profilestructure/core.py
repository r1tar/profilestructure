from __future__ import annotations

from collections import defaultdict
from typing import Any
from dataclasses import dataclass
from .exceptions import UnknownProfileError, UnsupportedTypeError, UnknownKeyError, DuplicatedKeyError

class ProfileStructure:
    def __init__(self, structure: dict[str, Any]|list[Any], profiles: dict[str, list[str|int]], default: Any = None):
        self._profiles = self._profile(structure, profiles, default)

    def _profile(self, structure: dict[str, Any]|list[Any], profiles: dict[str, list[str|int]], default: Any, unshare_values: bool = False) -> dict:
        """
        プロファイルをkeyとするdictを返す
        ex) {"p1": {...} "p2": {...}}
        profilesの値であるlist(以下keys)が複数のプロファイルから指定されている場合SharedKeyValueクラスを用いて共有される。
        共有/非共有化は専用methodを使用して行える。
        structureがlistの場合、keysはstructureのインデックスとして解釈される。

        """
        
        if isinstance(structure, dict):
            get_value_from_structure = lambda key: structure.get(key, default)
        elif isinstance(structure, list):
            get_value_from_structure = lambda i: structure[i] if 0 <= i < len(structure) else default
        else:
            raise UnsupportedTypeError("Structure must be a dict or list")

        # 値を共有するkeyのリストを作成
        # keyの重複があった場合暗黙的にset型を使用して解消する
        all_keys_in_profiles = [set(keys) for keys in list(profiles.values())]

        if unshare_values or len(profiles.keys()) < 2:
            # set.intersection()はset型がindexが扱いづらいのでtupleに統一
            keys_intersection = tuple()
            shared_value_classes = []
        else:
            keys_intersection = tuple(all_keys_in_profiles[0].intersection(*all_keys_in_profiles[1:]))
            shared_value_classes = [None for _ in keys_intersection] # list[SharedKeysValue]で後に置き換え


        profiles_key = defaultdict(dict)
        # TODO: ネストが深いのでリファクタリングする
        for profile, keys in profiles.items():
            for key in keys:
                # keyが共有されている場合、shared_value_classesから値を取得
                # 共有されていない場合はそのままstructureから取得し、インスタンスをshared_value_classesに追加
                if key in keys_intersection:
                    key_i = keys_intersection.index(key)
                    if shared_value_classes[key_i]:
                        # 共有されている値が存在する場合はそれを使用
                        value_to_assign = shared_value_classes[key_i]
                        shared_value_classes[key_i].keys.append([profile, key])
                    else:
                        # 共有されている値が存在しない場合は新しいSharedKeysValueを作成
                        value_to_assign = SharedKeysValue(keys=[[profile, key]], value=get_value_from_structure(key))
                        shared_value_classes[key_i] = value_to_assign
                else:
                    value_to_assign = get_value_from_structure(key)

                profiles_key[profile][key] = value_to_assign
        
        return dict(profiles_key)

    @property
    def profiles(self) -> dict[str, Any]:
        """
        Get the profiles.
        """
        return self._profiles
    
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
            return key in self.get(profile, default={})
        else:
            return profile in self._profiles
        
    def set(self, profile, value, key=None, allow_nonexistent_profile_and_key: bool = True) -> None:
        """
        Set the value for a specific profile.
        """
        if not self.has(profile, key):
            if not allow_nonexistent_profile_and_key:
                raise UnknownProfileError(f"Profile '{profile}' or key '{key}' does not exist.")
            self.create_profile(profile, {}, allow_existent_profile=True)

        # keyがNoneの場合(プロファイルの更新）を先に処理したほうがまとまりやすい
        if not key:
            # keyがNoneの場合はプロファイル全体を更新
            if isinstance(value, dict):
                self._profiles[profile] = value
                return
            else:
                raise UnsupportedTypeError("Value must be a dict when key is None")
            
        # keyの内容を更新
        unchanged_value = self.get(profile, key)
        if isinstance(unchanged_value, SharedKeysValue):
            # SharedKeysValueの場合は値を更新
            if [profile, key] not in unchanged_value.keys:
                unchanged_value.keys.append([profile, key])
            self._profiles[profile][key].value = value
        else:
            # 通常の値の場合はそのまま更新
            self._profiles[profile][key] = value

    def create_profile(self, profile, value=None, allow_existent_profile: bool = False) -> None:
        """
        Create a new profile.
        """
        if allow_existent_profile or not self.has(profile):
            self.set(profile, value, allow_nonexistent_profile_and_key=True)
        else:
            raise UnknownProfileError(f"Profile '{profile}' already exists.")

    def pop_profile(self, profile, default=None, allow_nonexistent_profile: bool = True) -> Any:
        """
        Delete a profile.
        """
        if not (self.has(profile) or allow_nonexistent_profile):
            raise UnknownProfileError(f"Profile '{profile}' does not exist.")
        return self._profiles.pop(profile, default) # 存在しない場合にdelを使用するとKeyErrorが発生する
    
    
    def delete_profile(self, profile, allow_nonexistent_profile: bool = True) -> None:
        """
        Delete a profile.
        """
        self.pop_profile(profile, None, allow_nonexistent_profile=allow_nonexistent_profile)

    def move_profile(self, key, old_profile, new_profile, allow_nonexistent_profile: bool = False) -> None:
        """
        Move a key from one profile to another.
        """
        # プロファイル変更対象が存在しないのでKeyErrorを送出
        if not self.has(old_profile, key):
            raise UnknownKeyError(f"Key '{key}' does not exist in profile '{old_profile}'.")

        # そうでなければ新しいプロファイルを作成
        if not self.has(new_profile):
            if not allow_nonexistent_profile:
                raise UnknownProfileError(f"Profile '{new_profile}' does not exist.")
            self.create_profile(new_profile, {}, allow_existent_profile=False)

        self.set(
            new_profile,
            self.pop_key(old_profile, key, default=None, allow_nonexisting_profile_and_key=False),
            key=key,
            allow_nonexistent_profile_and_key=False)
        
    def profile_names(self) -> list[str]:
        """
        Get a list of profile names.
        """
        return list(self._profiles.keys())
    
    def change_profile_name(self, old_name, new_name, overwrite: bool = False) -> None:
        """
        Change the name of a profile.
        """
        if not self.has(old_name):
            raise UnknownProfileError(f"Profile '{old_name}' does not exist.")

        if self.has(new_name):
            if not overwrite:
                raise UnknownProfileError(f"Profile '{new_name}' already exists.")

        self._profiles[new_name] = self._profiles.pop(old_name)
    
    def add_key(self, profile, key, value=None, overwrite: bool = False) -> None:
        """
        Add a key to a profile.
        """
        if not self.has(profile):
            raise UnknownProfileError(f"Profile '{profile}' does not exist.")

        if self.has(profile, key):
            if not overwrite:
                raise DuplicatedKeyError(f"Key '{key}' already exists in profile '{profile}'.")

        self.set(profile, value, key=key, allow_nonexistent_profile_and_key=True)

    def pop_key(self, profile, key, default=None, allow_nonexisting_profile_and_key: bool = True) -> Any:
        """
        Pop a key from a profile.
        """
        if not (self.has(profile, key) or allow_nonexisting_profile_and_key):
            raise UnknownKeyError(f"Key '{key}' or profile '{profile} does not exist.")

        return self.get(profile, default={}).pop(key, default)
    
    def remove_key(self, profile, key, allow_unexisting_profile_and_key: bool = True) -> None:
        """
        Remove a key from a profile.
        """
        self.pop_key(profile, key, default=None, allow_nonexisting_profile_and_key=allow_unexisting_profile_and_key)
        
    def key_names(self, profile) -> list[str]:
        """
        Get a list of key names for a specific profile.
        """
        if not self.has(profile):
            raise UnknownProfileError(f"Profile '{profile}' does not exist.")
        
        return list(self._profiles[profile].keys())
    
    def change_key_name(self, profile, old_name, new_name, overwrite: bool = False) -> None:
        """
        Change the name of a key in a profile.
        """
        if not self.has(profile, old_name):
            raise UnknownKeyError(f"Key '{old_name}' does not exist in profile '{profile}'.")

        if new_name in self._profiles[profile]:
            if not overwrite:
                raise DuplicatedKeyError(f"Key '{new_name}' already exists in profile '{profile}'.")

        self._profiles[profile][new_name] = self.get(profile).pop(old_name)

    def share_key_value(self, profile, key, other_keys: list[list[str, str|int]], overwrite: bool = False) -> None:
        """
        Share the value of a key across profiles.
        """
        if not self.has(profile, key):
            raise UnknownKeyError(f"Key '{key}' or profile '{profile}' does not exist.")

        # 共有されていない場合はSharedKeysValueに置き換える
        current_value = self.get(profile, key)
        if not isinstance(current_value, SharedKeysValue):
            if not isinstance(other_keys, list):
                raise UnsupportedTypeError("other_keys must be a list of keys to share.")
            shared_value = SharedKeysValue(keys=[[profile, key]] + other_keys, value=current_value)
            for skey in shared_value.keys:
                self.set(skey[0], shared_value, key=skey[1], allow_nonexistent_profile_and_key=True)

    def unshare_key_value(self, profile, key) -> None:
        """
        Unshare the value of a key in a profile.
        """
        if not self.has(profile, key):
            raise UnknownKeyError(f"Key '{key}' or profile '{profile}' does not exist.")

        current_value = self.get(profile, key)
        if isinstance(current_value, SharedKeysValue):
            for skey in current_value.keys:
                self.set(skey[0], current_value.value, key=skey[1], allow_nonexistent_profile_and_key=True)

    def asdict(self, allow_duplicates: bool = True) -> dict:
        """
        Return the structure as a dictionary.
        """
        key_contents = {}
        for profile_content in list(self._profiles.values()):
            for k, v in profile_content.items():
                if not allow_duplicates and k in key_contents:
                    raise DuplicatedKeyError(f"Duplicate key '{k}' found in profiles.")
                key_contents[k] = v
        return key_contents
    
    def aslist(self, default=None, allow_duplicates: bool = True) -> dict:
        """
        Return the structure as a list.
        """
        as_dict = self.as_dict(allow_duplicates)
        sorted_dict_keys = sorted(as_dict.keys())
        return [as_dict[i] if i in as_dict else default for i in sorted_dict_keys]

# 依存関係を極力減らしたいこと、値を共有するための最低限の機能のみあれば良いこと、listなどだと分かりにくくなるためdataclasses.dataclassを使用
@dataclass
class SharedKeysValue:
    """
    Represents a profile with its name and associated keys.
    """
    keys: list[list[str, str|int]] # list[profile, key]
    value: Any