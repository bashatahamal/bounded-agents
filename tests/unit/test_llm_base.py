from bounded.llm.base import image_message_content


def test_image_message_content_shape():
    content = image_message_content("describe this", "data:image/png;base64,xyz")

    assert content == [
        {"type": "text", "text": "describe this"},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,xyz"}},
    ]
