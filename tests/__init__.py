from unittest import TestCase

from profilestructure import ProfileStructure

class TestProfileStructure(TestCase):
    def setUp(self):
        self.structure = {
            "name": "default",
            "version": 1,
            "settings": {
                "theme": "light",
                "notifications": True
            }
        }
        self.profiles = {
            "user1": ["name", "settings"],
            "user2": ["version", "settings"]
        }
        self.profile_structure = ProfileStructure(self.structure, self.profiles)