# plugins/memory_summarize.py

import logging
from typing import Any, Dict

# Import dependencies
from src.adam.adapters import ChromaVectorStore
from src.adam.plugin_manager import manager

logger = logging.getLogger("adam")

METADATA = {
    "label": "Memory Summarizer",
    "description": "Retrieves all documents from memory and generates a summary.",
    "ui_action": False,
    "executable": True,
}


def run(**kwargs) -> Dict[str, Any]:
    """
    Retrieves all documents from the vector store, combines them,
    and uses an LLM plugin to generate a summary.
    """
    try:
        logger.info("Starting memory summarization...")

        # 1. Initialize vector store
        vector_store = ChromaVectorStore()

        # 2. Validate initialization
        if not hasattr(vector_store, "collection") or vector_store.collection is None:
            return {
                "ok": False,
                "data": None,
                "error": "Vector store failed to initialize. Check chromadb installation.",
            }

        # 3. Retrieve all documents
        try:
            memory_contents = vector_store.collection.get()
        except Exception as e:
            logger.error(f"Failed to retrieve memory contents: {e}")
            return {
                "ok": False,
                "data": None,
                "error": f"Vector store retrieval failed: {str(e)}",
            }

        documents = memory_contents.get("documents")
        if not documents:
            logger.info("Memory is empty. Returning empty summary.")
            return {"ok": True, "data": "The memory is currently empty.", "error": None}

        doc_count = len(documents)
        logger.info(f"Retrieved {doc_count} document chunks from memory.")

        # 4. Combine documents
        full_context = "\n\n---\n\n".join(documents)

        # 5. Create summarization prompt
        prompt = (
            "You are a summarization engine. Below is a collection of text chunks "
            "retrieved from a long-term memory store. Your task is to synthesize this "
            "information into a concise, high-level summary. Focus on the key themes, "
            "decisions, and topics present in the text.\n\n"
            "MEMORY CONTENTS:\n"
            "------------------\n"
            f"{full_context}\n"
            "------------------\n\n"
            "SUMMARY:"
        )

        # 6. Generate summary via LLM plugin
        logger.info("Calling local_llm plugin for summarization...")
        llm_result = manager.run_plugin(
            "local_llm", prompt=prompt, max_tokens=512, temperature=0.5, stream=False
        )

        if not llm_result.get("ok"):
            logger.error(f"LLM summarization failed: {llm_result.get('error')}")
            return llm_result  # ← FIXED TYPO: was ll_result

        summary = llm_result.get("data", "Failed to generate a summary.")
        final_report = f"Summary of {doc_count} memory entries:\n\n{summary}"
        logger.info("Memory summarization completed successfully.")

        return {"ok": True, "data": final_report, "error": None}

    except Exception as e:
        error_msg = f"Memory summarization failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"ok": False, "data": None, "error": error_msg}
