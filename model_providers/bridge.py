from __future__ import annotations
import json, re
from functools import partial
from batch_runner import BatchCase, CaseExecutionResult
from .core import ModelRequest, ModelProvider

def _parse(text):
    value=None
    try: value=json.loads(text.strip())
    except json.JSONDecodeError:
        match=re.search(r"\{.*\}",text,re.DOTALL)
        if match:
            try: value=json.loads(match.group(0))
            except json.JSONDecodeError: value=None
    if isinstance(value,dict):
        p=value.get("prediction"); c=value.get("confidence")
        return (p if isinstance(p,int) else None,
                c if isinstance(c,int) and 0<=c<=100 else None)
    match=re.search(r"(?<!\d)-?\d+(?!\d)",text)
    return (int(match.group()) if match else None,None)

class ProviderExecutor:
    def __init__(self, provider: ModelProvider, prompt_builder):
        self.provider=provider; self.prompt_builder=prompt_builder
    def __call__(self, case: BatchCase):
        response=self.provider.generate(self.prompt_builder(case))
        prediction,confidence=_parse(response.text)
        actual=case.payload.get("actual_value")
        actual=actual if isinstance(actual,int) else None
        return CaseExecutionResult(
            response_text=response.text, parsed_prediction=prediction,
            actual_value=actual,
            is_correct=(prediction==actual if prediction is not None and actual is not None else None),
            confidence=confidence, latency_seconds=response.latency_seconds,
            successful=prediction is not None, provider_request_id=response.request_id,
            metadata={"provider":response.provider,"provider_model":response.model,
                      "finish_reason":response.finish_reason,"usage":response.usage.to_dict()}
        )

def payload_prompt_builder(case: BatchCase, *, default_model, default_system_prompt=None):
    prompt=case.payload.get("prompt")
    if not isinstance(prompt,str) or not prompt.strip(): raise ValueError("Case payload requires prompt.")
    return ModelRequest(
        prompt=prompt, model=str(case.payload.get("model",default_model)),
        system_prompt=case.payload.get("system_prompt",default_system_prompt),
        temperature=float(case.payload.get("temperature",0.0)),
        max_output_tokens=case.payload.get("max_output_tokens"),
        seed=case.payload.get("seed"), json_mode=bool(case.payload.get("json_mode",True)),
        metadata={"case_id":case.case_id,"prompt_sha256":case.prompt_sha256}
    )
