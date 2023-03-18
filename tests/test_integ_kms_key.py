import pytest

from clean_orphaned_resources.app import CleanOrphanedResources


class TestIntegKmsKey:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.app = CleanOrphanedResources()

    def test_list_and_destroy(self, capfd):
        """
        KMS Keys cannot be deleted immediately, we are currently verifying them manually.
        """
        pass
