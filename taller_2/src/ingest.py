"""Reconstruye chroma_db/ desde cero: python -m src.ingest"""
import shutil
from collections import Counter

from src.chunking import load_chunks
from src.config import CHROMA_DIR
from src.retriever import get_store


def main() -> None:
    chunks = load_chunks()
    # Se borra la base anterior para que no queden fragmentos de documentos que ya cambiaron
    # No se ignoran los errores: en Windows falla si otro proceso (p. ej. el chat) tiene abierta la base,
    # y seguir adelante dejaría fragmentos viejos mezclados con los nuevos.
    if CHROMA_DIR.exists():
        try:
            shutil.rmtree(CHROMA_DIR)
        except OSError as e:
            raise SystemExit(f"No se pudo borrar {CHROMA_DIR.name}/ ({e}). "
                             "Cierra el chat u otros procesos que usen la base y vuelve a ejecutar.")
    store = get_store()
    # ids deterministas = chunk_id: reindexar sobreescribe en vez de duplicar
    store.add_documents(chunks, ids=[c.metadata["chunk_id"] for c in chunks])
    print(f"Indexados {len(chunks)} fragmentos en {CHROMA_DIR.name}/")
    for doc_type, n in Counter(c.metadata["doc_type"] for c in chunks).items():
        print(f"  {doc_type}: {n}")


if __name__ == "__main__":
    main()
