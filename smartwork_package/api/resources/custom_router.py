import time
from typing import Callable

from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.routing import APIRoute

from elasticsearch import Elasticsearch
from api.resources.constants import ES_PASSWORD,ES_URL


es = Elasticsearch(ES_URL,basic_auth=("elastic",ES_PASSWORD),verify_certs=False)

class LoggingRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            if request.method=="POST":
                if not es.indices.exists(index="log"):
                    es.indices.create(index = 'log')
                es.index(index="log",document={"body":str( await request.body())})
            response: Response = await original_route_handler(request)
            return response

        return custom_route_handler
