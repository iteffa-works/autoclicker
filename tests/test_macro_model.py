from app.models.macro import MacroDefinition, MacroEvent, MacroEventType


def test_macro_roundtrip_json() -> None:
    m = MacroDefinition(
        name="t",
        events=[
            MacroEvent(kind=MacroEventType.KEY_DOWN, delay_ms=10, key="a"),
            MacroEvent(kind=MacroEventType.KEY_UP, delay_ms=5, key="a"),
        ],
    )
    d = m.to_dict()
    m2 = MacroDefinition.from_dict(d)
    assert m2.name == "t"
    assert len(m2.events) == 2
    assert m2.events[0].kind == MacroEventType.KEY_DOWN
