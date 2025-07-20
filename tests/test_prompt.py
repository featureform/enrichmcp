from unittest.mock import Mock

from enrichmcp import EnrichMCP


def test_prompt_delegates_to_fastmcp():
    app = EnrichMCP("Title", description="desc")
    decorator = Mock(side_effect=lambda f: f)
    app.mcp.prompt = Mock(return_value=decorator)

    @app.prompt(name="foo", title="Foo", description="bar")
    def fn():
        pass

    app.mcp.prompt.assert_called_once_with(name="foo", title="Foo", description="bar")
    decorator.assert_called_once_with(fn)
    assert fn.__name__ == "fn"
