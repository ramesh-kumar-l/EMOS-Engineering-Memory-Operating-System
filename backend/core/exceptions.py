from fastapi import HTTPException


class EMOSError(Exception):
    pass


class DocumentNotFoundError(EMOSError):
    def __init__(self, slug: str) -> None:
        self.slug = slug
        super().__init__(f"Document '{slug}' not found")


class DocumentAlreadyExistsError(EMOSError):
    def __init__(self, slug: str) -> None:
        self.slug = slug
        super().__init__(f"Document '{slug}' already exists")


class FileSystemError(EMOSError):
    pass


class IndexNotReadyError(EMOSError):
    def __init__(self) -> None:
        super().__init__("FAISS index has not been built yet. POST /api/v1/retrieval/index first.")


class ClaudeNotConfiguredError(EMOSError):
    def __init__(self) -> None:
        super().__init__(
            "Claude API key is not configured. Set ANTHROPIC_API_KEY in .env "
            "or omit send_to_claude from the request."
        )


class PromptNotFoundError(EMOSError):
    def __init__(self, slug: str) -> None:
        self.slug = slug
        super().__init__(f"Prompt template '{slug}' not found")


class PromptAlreadyExistsError(EMOSError):
    def __init__(self, slug: str) -> None:
        self.slug = slug
        super().__init__(f"Prompt template '{slug}' already exists")


class PromptRenderError(EMOSError):
    def __init__(self, missing: list[str]) -> None:
        self.missing = missing
        super().__init__(f"Missing required parameters: {', '.join(missing)}")


class WorkflowNotFoundError(EMOSError):
    def __init__(self, workflow_id: str) -> None:
        self.workflow_id = workflow_id
        super().__init__(f"Workflow definition '{workflow_id}' not found")


class WorkflowRunNotFoundError(EMOSError):
    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        super().__init__(f"Workflow run '{run_id}' not found")


class WorkflowInvalidStateError(EMOSError):
    def __init__(self, run_id: str, current_status: str) -> None:
        self.run_id = run_id
        self.current_status = current_status
        super().__init__(f"Workflow run '{run_id}' is {current_status} and cannot be modified")


class RepoPathNotFoundError(EMOSError):
    def __init__(self, msg: str) -> None:
        super().__init__(msg)


class RepoInvalidPathError(EMOSError):
    def __init__(self, msg: str) -> None:
        super().__init__(msg)


def to_http(exc: EMOSError) -> HTTPException:
    if isinstance(exc, DocumentNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, DocumentAlreadyExistsError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, IndexNotReadyError):
        return HTTPException(status_code=503, detail=str(exc))
    if isinstance(exc, ClaudeNotConfiguredError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, PromptNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, PromptAlreadyExistsError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, PromptRenderError):
        return HTTPException(status_code=422, detail=str(exc))
    if isinstance(exc, WorkflowNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, WorkflowRunNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, WorkflowInvalidStateError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, RepoPathNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, RepoInvalidPathError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, FileSystemError):
        return HTTPException(status_code=500, detail=str(exc))
    return HTTPException(status_code=500, detail=str(exc))
