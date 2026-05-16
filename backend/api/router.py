from fastapi import APIRouter

from .v1 import context, health, memory, prompts, repo, retrieval, workflows

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(memory.router)
api_router.include_router(retrieval.router)
api_router.include_router(context.router)
api_router.include_router(prompts.router)
api_router.include_router(workflows.router)
api_router.include_router(repo.router)
