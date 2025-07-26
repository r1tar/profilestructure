import unittest
from unittest import TestCase
from pprint import pprint

from profilestructure import ProfileStructure

class TestProfileStructureWithDict(TestCase):
    def setUp(self):
        self.test_data = {
            "name": "Test Profile",
            "version": "1.0",
            "description": "This is a test profile structure.",
            "fields": [
                {"name": "field1", "type": "string"},
                {"name": "field2", "type": "integer"},
                {"name": "field3", "type": "boolean"}
            ]
        }

        self.test_profiles = {
            "admin": ["name", "version", "description", "fields"],
            "viewer": ["name", "version", "description"],
            "database": ["fields"]
        }

        self.profile_structure = ProfileStructure(self.test_data, self.test_profiles)

    def tearDown(self):
        del self.profile_structure
        del self.test_data
        del self.test_profiles
    
    def test_get_profile_structure(self):
        # pprint(self.profile_structure.profiles)
        pass

    def test_has_profile(self):
        for profile in self.test_profiles:
            self.assertTrue(self.profile_structure.has(profile), f"Profile '{profile}' should exist.")
        
        self.assertFalse(self.profile_structure.has("non_existent_profile"), "Profile 'non_existent_profile' should not exist.")
    
    def test_get_profile(self):
        for profile in self.test_profiles:
            data = self.profile_structure.get(profile)
            self.assertIsInstance(data, dict, f"Data for profile '{profile}' should be a dictionary.")
            self.assertTrue(set(data.keys()).issubset(set(self.test_profiles[profile])), f"Keys in profile '{profile}' should match the expected keys.")

    def test_get_profile_names(self):
        profile_names = self.profile_structure.profile_names()
        self.assertTrue(isinstance(profile_names, list), "Profile names should be a list.")
        for profile in self.test_profiles:
            self.assertIn(profile, profile_names, f"Profile '{profile}' should be in the profile names list.")

    def test_get_profile_data(self):
        for profile in self.test_profiles:
            data = self.profile_structure.get(profile)
            self.assertIsInstance(data, dict, f"Data for profile '{profile}' should be a dictionary.")
            self.assertTrue(set(data.keys()).issubset(set(self.test_profiles[profile])), f"Keys in profile '{profile}' should match the expected keys.")

    def test_get_profile_keys(self):
        for profile in self.test_profiles:
            keys = self.profile_structure.key_names(profile)
            self.assertTrue(set(keys).issubset(set(self.test_profiles[profile])))

    def test_change_profile_name(self):
        old_name = "admin"
        new_name = "administrator"

        unchanged_data = self.profile_structure.get(old_name)

        self.profile_structure.change_profile_name(old_name, new_name)

        self.assertIn(new_name, self.profile_structure.profile_names())
        self.assertNotIn(old_name, self.profile_structure.profile_names())
        self.assertEqual(self.profile_structure.get(new_name), unchanged_data)

    def test_change_key_name(self):
        profile = "admin"
        old_key = "name"
        new_key = "name_corrected"

        unchanged_value = self.profile_structure.get(profile, old_key)

        self.profile_structure.change_key_name(profile, old_key, new_key, overwrite=False)

        self.assertIn(new_key, self.profile_structure.key_names(profile))
        self.assertNotIn(old_key, self.profile_structure.key_names(profile))
        data_after_key_changed = self.profile_structure.get(profile, new_key)
        self.assertEqual(data_after_key_changed, unchanged_value)

        self.profile_structure.change_key_name(profile, new_key, old_key, overwrite=True)

        self.assertIn(old_key, self.profile_structure.key_names(profile))
        self.assertNotIn(new_key, self.profile_structure.key_names(profile))
        self.assertEqual(data_after_key_changed, unchanged_value)

if __name__ == "__main__":
    unittest.main()