def assert_contents_equal(content1, content2):
    if isinstance(content1, bytes):
        content1 = content1.decode("utf-8")
    if isinstance(content2, bytes):
        content2 = content2.decode("utf-8")
    content1 = content1.replace("\r\n", "\n")
    content2 = content2.replace("\r\n", "\n")
    assert content1 == content2
