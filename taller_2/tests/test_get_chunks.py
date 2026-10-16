from src.retriever import get_chunks


def test_get_chunks_sin_ids_no_toca_chroma():
    class StoreQueNoDebeUsarse:
        def get(self, *args, **kwargs):
            raise AssertionError("no debería consultarse Chroma con una lista vacía")

    assert get_chunks([], StoreQueNoDebeUsarse()) == []
