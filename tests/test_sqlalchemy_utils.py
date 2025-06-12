from datetime import time
from typing import Any

from sqlalchemy import JSON, Integer, LargeBinary, Time
from sqlalchemy.sql.type_api import TypeEngine

from enrichmcp.sqlalchemy.mixin import _sqlalchemy_type_to_python


def test_sqlalchemy_type_to_python_extra_types():
    assert _sqlalchemy_type_to_python(JSON()) is dict
    assert _sqlalchemy_type_to_python(LargeBinary()) is bytes
    assert _sqlalchemy_type_to_python(Time()) is time

    class MyInt(Integer):
        pass

    assert _sqlalchemy_type_to_python(MyInt()) is int

    class Custom(TypeEngine):
        pass

    assert _sqlalchemy_type_to_python(Custom()) is Any
