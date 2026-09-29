import pytest
from app.connectors.base import RepositoryConnector


class IncompleteConnector(RepositoryConnector):
    pass


def test_incomplete_connector_cannot_be_created():
    with pytest.raises(TypeError):
        IncompleteConnector()
        