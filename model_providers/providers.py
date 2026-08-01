from __future__ import annotations
import json, os, time
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import quote
from .core import ModelRequest, ProviderCapabilities, ProviderResponse, ProviderUsage
from .transport import JsonTransport, UrllibJsonTransport

def _env(name):
    value = os.getenv(name)
    if not value: raise RuntimeError(f"Required environment variable is not set: {name}")
    return value

def _usage(source, a, b, c):
    if not isinstance(source, Mapping): source = {}
    val = lambda key: source.get(key) if isinstance(source.get(key), int) else None
    x, y, z = val(a), val(b), val(c)
    if z is None and x is not None and y is not None: z = x + y
    return ProviderUsage(x, y, z)

class _HttpBase:
    def __init__(self, *, transport=None, timeout_seconds=120.0, clock=time.perf_counter):
        self.transport = transport or UrllibJsonTransport()
        self.timeout_seconds = timeout_seconds
        self.clock = clock
    def _post(self, url, headers, body):
        started = self.clock()
        response = self.transport.post_json(
            url, headers=headers, body=body, timeout_seconds=self.timeout_seconds
        )
        return response, max(0.0, self.clock() - started)

class OpenAIProvider(_HttpBase):
    name = "openai"
    capabilities = ProviderCapabilities(True, True, False)
    def __init__(self, *, api_key=None, endpoint="https://api.openai.com/v1/responses", **kw):
        super().__init__(**kw); self.api_key=api_key; self.endpoint=endpoint
    def generate(self, request):
        body={"model":request.model,"input":request.prompt}
        if request.system_prompt: body["instructions"]=request.system_prompt
        if request.temperature is not None: body["temperature"]=request.temperature
        if request.max_output_tokens: body["max_output_tokens"]=request.max_output_tokens
        if request.json_mode: body["text"]={"format":{"type":"json_object"}}
        response, latency=self._post(
            self.endpoint, {"Authorization":f"Bearer {self.api_key or _env('OPENAI_API_KEY')}"}, body
        )
        doc=response.body; text=doc.get("output_text")
        if not isinstance(text,str):
            parts=[]
            for item in doc.get("output",[]) if isinstance(doc.get("output"),list) else []:
                for part in item.get("content",[]) if isinstance(item,dict) else []:
                    if isinstance(part,dict) and isinstance(part.get("text"),str): parts.append(part["text"])
            text="".join(parts)
        if not text: raise RuntimeError("OpenAI response contains no text.")
        return ProviderResponse(
            self.name, str(doc.get("model",request.model)), text, latency,
            str(doc["id"]) if isinstance(doc.get("id"),str) else response.headers.get("x-request-id"),
            str(doc["status"]) if isinstance(doc.get("status"),str) else None,
            _usage(doc.get("usage"),"input_tokens","output_tokens","total_tokens"), dict(doc)
        )

class AnthropicProvider(_HttpBase):
    name = "anthropic"
    capabilities = ProviderCapabilities(True, False, False)
    def __init__(self, *, api_key=None, endpoint="https://api.anthropic.com/v1/messages",
                 api_version="2023-06-01", **kw):
        super().__init__(**kw); self.api_key=api_key; self.endpoint=endpoint; self.api_version=api_version
    def generate(self, request):
        body={"model":request.model,"messages":[{"role":"user","content":request.prompt}],
              "max_tokens":request.max_output_tokens or 1024}
        if request.system_prompt: body["system"]=request.system_prompt
        if request.temperature is not None: body["temperature"]=request.temperature
        response, latency=self._post(
            self.endpoint, {"x-api-key":self.api_key or _env("ANTHROPIC_API_KEY"),
                            "anthropic-version":self.api_version}, body
        )
        doc=response.body
        text="".join(
            block["text"] for block in doc.get("content",[])
            if isinstance(block,dict) and block.get("type")=="text" and isinstance(block.get("text"),str)
        )
        if not text: raise RuntimeError("Anthropic response contains no text.")
        return ProviderResponse(
            self.name, str(doc.get("model",request.model)), text, latency,
            str(doc["id"]) if isinstance(doc.get("id"),str) else response.headers.get("request-id"),
            str(doc["stop_reason"]) if isinstance(doc.get("stop_reason"),str) else None,
            _usage(doc.get("usage"),"input_tokens","output_tokens","total_tokens"), dict(doc)
        )

class GeminiProvider(_HttpBase):
    name = "gemini"
    capabilities = ProviderCapabilities(True, True, False)
    def __init__(self, *, api_key=None,
                 endpoint_template="https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                 **kw):
        super().__init__(**kw); self.api_key=api_key; self.endpoint_template=endpoint_template
    def generate(self, request):
        config={}
        if request.temperature is not None: config["temperature"]=request.temperature
        if request.max_output_tokens: config["maxOutputTokens"]=request.max_output_tokens
        if request.json_mode: config["responseMimeType"]="application/json"
        body={"contents":[{"role":"user","parts":[{"text":request.prompt}]}]}
        if config: body["generationConfig"]=config
        if request.system_prompt: body["systemInstruction"]={"parts":[{"text":request.system_prompt}]}
        endpoint=self.endpoint_template.format(model=quote(request.model,safe=""))
        response, latency=self._post(
            endpoint, {"x-goog-api-key":self.api_key or _env("GEMINI_API_KEY")}, body
        )
        doc=response.body
        candidates=doc.get("candidates",[])
        first=candidates[0] if isinstance(candidates,list) and candidates else {}
        parts=first.get("content",{}).get("parts",[]) if isinstance(first,dict) else []
        text="".join(p["text"] for p in parts if isinstance(p,dict) and isinstance(p.get("text"),str))
        if not text: raise RuntimeError("Gemini response contains no text.")
        return ProviderResponse(
            self.name, request.model, text, latency, None,
            str(first["finishReason"]) if isinstance(first.get("finishReason"),str) else None,
            _usage(doc.get("usageMetadata"),"promptTokenCount","candidatesTokenCount","totalTokenCount"),
            dict(doc)
        )

class GenericHttpProvider(_HttpBase):
    name="http"
    capabilities=ProviderCapabilities(True,True,True)
    def __init__(self, endpoint, *, headers=None, text_path=("text",), **kw):
        super().__init__(**kw); self.endpoint=endpoint; self.headers=dict(headers or {}); self.text_path=tuple(text_path)
    def generate(self, request):
        body={"prompt":request.prompt,"model":request.model,"system_prompt":request.system_prompt,
              "temperature":request.temperature,"max_output_tokens":request.max_output_tokens,
              "seed":request.seed,"json_mode":request.json_mode,"metadata":dict(request.metadata)}
        response, latency=self._post(self.endpoint,self.headers,body); doc=response.body; value=doc
        for key in self.text_path:
            value=value.get(key) if isinstance(value,Mapping) else None
        if not isinstance(value,str): raise RuntimeError("Configured text_path did not resolve to text.")
        return ProviderResponse(
            self.name, str(doc.get("model",request.model)), value, latency,
            doc.get("request_id") if isinstance(doc.get("request_id"),str) else None,
            doc.get("finish_reason") if isinstance(doc.get("finish_reason"),str) else None,
            _usage(doc.get("usage"),"input_tokens","output_tokens","total_tokens"), dict(doc)
        )

class ManualResponseProvider:
    name="manual"
    capabilities=ProviderCapabilities(True,True,True)
    def __init__(self, response_store):
        self.path=Path(response_store); self.responses={}
        lines=self.path.read_text(encoding="utf-8-sig").splitlines()
        values=[json.loads(line) for line in lines if line.strip()] if self.path.suffix.lower()==".jsonl" else json.loads(self.path.read_text(encoding="utf-8-sig"))
        if isinstance(values,dict): values=[values]
        for item in values:
            key=item.get("case_id",item.get("prompt_sha256"))
            if not isinstance(key,str): raise ValueError("Manual response requires case_id or prompt_sha256.")
            self.responses[key]=item
    def generate(self, request):
        item=None
        for key in (request.metadata.get("case_id"),request.metadata.get("prompt_sha256")):
            if isinstance(key,str) and key in self.responses: item=self.responses[key]; break
        if item is None: raise RuntimeError("No manual response found.")
        text=item.get("text",item.get("response_text"))
        if not isinstance(text,str): raise RuntimeError("Manual response contains no text.")
        return ProviderResponse(
            self.name,str(item.get("model",request.model)),text,0.0,
            item.get("request_id") if isinstance(item.get("request_id"),str) else None,
            item.get("finish_reason") if isinstance(item.get("finish_reason"),str) else None,
            ProviderUsage(),dict(item)
        )
