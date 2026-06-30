from pathlib import Path

import pydantic

from dagri_subtask1_baseline.shared.llm_client import (
    LLMRuntime,
    build_json_schema_format,
)


class _OutputModel(pydantic.BaseModel):
    value: str


class _Response:
    def __init__(self, output_text: str):
        self.output_text = output_text


class _ResponsesClient:
    def __init__(self):
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return _Response('{"value": "ok"}')


class _Client:
    def __init__(self):
        self.responses = _ResponsesClient()


def test_request_json_multimodal_sends_text_and_image(tmp_path):
    image_path = tmp_path / "page-1.png"
    image_path.write_bytes(b"png")

    client = _Client()
    runtime = LLMRuntime(client=client, model="dummy-model")

    actual = runtime.request_json_multimodal(
        system_prompt="system",
        page_inputs=[
            {"page_number": 1, "text": "ocr", "image_path": image_path},
        ],
        instructions="instructions",
        response_model=_OutputModel,
    )

    assert actual.value == "ok"
    user_content = client.responses.last_kwargs["input"][1]["content"]
    assert any(item.get("type") == "input_text" for item in user_content)
    assert any(item.get("type") == "input_image" for item in user_content)


def test_build_json_schema_format_sets_additional_properties_false():
    class _InnerModel(pydantic.BaseModel):
        value: str

    class _OuterModel(pydantic.BaseModel):
        items: list[_InnerModel]

    text_format = build_json_schema_format(name="outer", response_model=_OuterModel)
    schema = text_format["schema"]

    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert schema["required"] == ["items"]
    assert schema["$defs"]["_InnerModel"]["type"] == "object"
    assert schema["$defs"]["_InnerModel"]["additionalProperties"] is False
    assert schema["$defs"]["_InnerModel"]["required"] == ["value"]


def test_build_json_schema_format_sets_required_to_all_properties():
    class _ItemModel(pydantic.BaseModel):
        id: str | None = None
        name: str

    class _ContainerModel(pydantic.BaseModel):
        items: list[_ItemModel]

    text_format = build_json_schema_format(name="container", response_model=_ContainerModel)
    item_schema = text_format["schema"]["$defs"]["_ItemModel"]

    assert set(item_schema["properties"].keys()) == {"id", "name"}
    assert item_schema["required"] == ["id", "name"]


def test_request_json_sends_text_format():
    client = _Client()
    runtime = LLMRuntime(client=client, model="dummy-model")
    text_format = build_json_schema_format(name="output", response_model=_OutputModel)

    actual = runtime.request_json(
        system_prompt="system",
        user_prompt="user",
        response_model=_OutputModel,
        text_format=text_format,
    )

    assert actual.value == "ok"
    assert client.responses.last_kwargs["text"]["format"] == text_format
    assert (
        client.responses.last_kwargs["text"]["format"]["schema"]["additionalProperties"]
        is False
    )


def test_request_json_multimodal_sends_text_format(tmp_path):
    image_path = tmp_path / "page-1.png"
    image_path.write_bytes(b"png")
    client = _Client()
    runtime = LLMRuntime(client=client, model="dummy-model")
    text_format = build_json_schema_format(name="output", response_model=_OutputModel)

    _ = runtime.request_json_multimodal(
        system_prompt="system",
        page_inputs=[{"page_number": 1, "text": "ocr", "image_path": image_path}],
        instructions="instructions",
        response_model=_OutputModel,
        text_format=text_format,
    )

    assert client.responses.last_kwargs["text"]["format"] == text_format


def test_build_json_schema_format_allows_decimal_for_capital_equipment_amount():
    class _CapitalEquipmentModel(pydantic.BaseModel):
        amount: int | float | None = None

    text_format = build_json_schema_format(
        name="capital_equipment",
        response_model=_CapitalEquipmentModel,
    )
    amount_schema = text_format["schema"]["properties"]["amount"]
    any_of = amount_schema.get("anyOf", [])
    types = {item.get("type") for item in any_of if isinstance(item, dict)}

    assert "integer" in types
    assert "number" in types
