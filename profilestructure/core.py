from __future__ import annotations

from collections import defaultdict
from typing import Any
from dataclasses import dataclass
from .exceptions import UnknownProfileError, UnsupportedTypeError, UnknownKeyError, DuplicatedKeyError

class ProfileStructure:
    def __init__(self, structure: dict[str, Any]|list[Any], profiles: dict[str, list[str|int]], default: Any = None):
        self._profiles = self._profile(structure, profiles, default)

    def _profile(self, structure: dict[str, Any]|list[Any], profiles: dict[str, list[str|int]], default: Any) -> dict:
        """
        プロファイルをkeyとするdictを返す
        ex) {"p1": {...} "p2": {...}}

        structureがlistの場合、それぞれのprofileの値であるリストの内容はstructureのインデックスとして解釈される。
        """
        # TODO: 複数のプロファイルが同じkeyを指定した場合の挙動をどうするかを決定する
        # 同じ値を共有するように実装したいがコストが嵩む
        # また、一度ｐrofileやkeyが消去された場合の挙動も決定する必要がある
        # 現在はそれぞれに値を代入しているので変更があった際に同期されない
        # 案1: 重複を許可しないようにする                                   あり得ない
        # 案2: 重複を許可し、重複するkeyの値を別に保持して変更時に反映させる   複雑化、変更時のコストが増える　listやclassなどを使用すれば単純化できる
        # 案3: 重複を許可し、別の値として扱う                                一番シンプルで分かりやすい
        # 結論: 案2を採用しSharedKeysValueクラスを使用して値を共有することに決定

        # 値を共有するkeyのリストを作成
        all_keys_in_profiles = [set(keys_list) for keys_list in list(profiles.values())]
        if len(profiles.keys()) < 2:
            # set.intersection()はset型がindexが扱いづらいのでtupleに統一
            keys_intersection = tuple()
            shared_values = []
        else:
            keys_intersection = tuple(all_keys_in_profiles[0].intersection(*all_keys_in_profiles[1:]))
            shared_values = [None for _ in keys_intersection] # list[SharedKeysValue]で後に置き換え

        if isinstance(structure, dict):
            get_value_from_structure = lambda key: structure.get(key, default)
        elif isinstance(structure, list):
            get_value_from_structure = lambda i: structure[i] if 0 <= i < len(structure) else default
        else:
            raise UnsupportedTypeError("Structure must be a dict or list")

        profiles_key = defaultdict(dict)
        # TODO: ネストが深いのでリファクタリングする
        for profile, keys in profiles.items():
            for key in keys:
                if profile not in profiles_key:
                    self.create_profile(profile, {}, strict=True)

                # keyが共有されている場合、shared_valuesから値を取得
                # 共有されていない場合はそのままstructureから取得し、インスタンスをshared_valuesに追加
                if key in keys_intersection:
                    key_i = keys_intersection.index(key)
                    if shared_values[key_i]:
                        # 共有されている値が存在する場合はそれを使用
                        value_to_assign = shared_values[key_i]
                        shared_values[key_i].keys.append(key)
                    else:
                        # 共有されている値が存在しない場合は新しいSharedKeysValueを作成
                        value_to_assign = SharedKeysValue(keys=[key], value=get_value_from_structure(key))
                        shared_values[key_i] = value_to_assign
                else:
                    value_to_assign = get_value_from_structure(key)

                profiles_key[profile][key] = value_to_assign
        
        return dict(profiles_key)
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
            raise UnknownKeyError(f"Key '{key}' does not exist in profile '{old_profile}'.")

        # 新しいプロファイルが存在しない場合、strictがTrueならUnknownProfileErrorを送出
        # そうでなければ新しいプロファイルを作成
        if not self.has(new_profile):
            if strict:
                raise UnknownProfileError(f"Profile '{new_profile}' does not exist.")
            self.create_profile(new_profile, {}, strict=True)

        self._profiles[new_profile][key] = self._profiles[old_profile].pop(key)

    def change_profile_name(self, profile, new_name, overwrite: bool = False) -> None:
        """
        Change the name of a profile.
        """
        if not self.has(profile):
            raise UnknownProfileError(f"Profile '{profile}' does not exist.")

        if self.has(new_name):
            if not overwrite:
                raise UnknownProfileError(f"Profile '{new_name}' already exists.")

        self._profiles[new_name] = self._profiles.pop(profile)
    
    def change_key_name(self, profile, key, new_name, overwrite: bool = False) -> None:
        """
        Change the name of a key in a profile.
        """
        if not self.has(profile, key):
            raise UnknownKeyError(f"Key '{key}' does not exist in profile '{profile}'.")

        if new_name in self._profiles[profile]:
            if not overwrite:
                raise DuplicatedKeyError(f"Key '{new_name}' already exists in profile '{profile}'.")

        self._profiles[profile][new_name] = self.get(profile).pop(key)

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
    keys: list[str|int] # key消去後にも値を保持するためのリスト
    value: Any