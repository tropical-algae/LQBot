# import json
# from typing import Optional
# import ast
# from qq_bot.basekit.logging import logger
# from qq_bot.service.chat_gpt.base import OpenAIBase
# from qq_bot.basekit.config import settings


# class VectorQueryGPT(OpenAIBase):
#     def __init__(self, base_url, api_key, prompt_path, default_model, max_retries = 3, **kwargs):
#         super().__init__(base_url, api_key, prompt_path, default_model, max_retries, **kwargs)
#         self.capture_knowlg_prompt: str = self.raw_instruct["instruct_capture_knowledge"]
    
#     async def capture_relation_knowledge(self, input: dict, model: Optional[str] = None, **kwargs) -> dict[int, float]:
#         try:
#             logger.info(f"[VectorQuery] Origin input: {input}")
#             content = self._set_prompt(input, self.prompt)
#             output = await self._async_inference(content=content, model=model, **kwargs)
#             return ast.literal_eval(output)
#         except Exception as err:
#             logger.error(f"An error has been found when capturing knowledge: {err}")
#             return {}
    
#     async def run(self, input: dict, model: Optional[str] = None, **kwargs) -> str:
#         logger.info(f"[VectorQuery] Processed input: {input}")
#         content = self._set_prompt(input, self.capture_knowlg_prompt)
#         output = await self._async_inference(content=content, model=model, **kwargs)

#         logger.info(f"[VectorQuery] GPT output: {output}")
#         return output


# vector_query_gpt = VectorQueryGPT(
#     base_url=settings.GPT_BASE_URL,
#     api_key=settings.GPT_API_KEY,
#     prompt_path=settings.VECTOR_QUERY_GPT_PROMPT,
#     default_model=settings.GPT_DEFAULT_MODEL
# )
vector_query_gpt = None