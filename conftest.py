import pytest


@pytest.fixture
def app():
    import ascribe
    app = ascribe.app
    app.config['TESTING'] = True
    return app
