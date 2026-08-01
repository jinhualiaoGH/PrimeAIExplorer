from __future__ import annotations
import hashlib, json
from batch_runner import BatchCase
from model_providers import *
from model_providers.transport import HttpJsonResponse

class FakeTransport:
    def __init__(self,body): self.body=body; self.calls=[]
    def post_json(self,url,*,headers,body,timeout_seconds):
        self.calls.append((url,dict(headers),dict(body)))
        return HttpJsonResponse(200,{},self.body)

def request():
    return ModelRequest("Predict.","model","Return JSON.",0,50,None,True)

def test_openai():
    p=OpenAIProvider(api_key="x",transport=FakeTransport(
        {"id":"r","model":"model","status":"completed","output_text":"{\"prediction\":6}",
         "usage":{"input_tokens":1,"output_tokens":2,"total_tokens":3}}),
         clock=iter((1.0,1.5)).__next__)
    r=p.generate(request()); assert r.text.startswith("{") and r.latency_seconds==0.5

def test_anthropic():
    p=AnthropicProvider(api_key="x",transport=FakeTransport(
        {"id":"m","model":"model","stop_reason":"end_turn",
         "content":[{"type":"text","text":"{\"prediction\":8}"}],
         "usage":{"input_tokens":2,"output_tokens":1}}),
         clock=iter((1.0,1.1)).__next__)
    assert p.generate(request()).usage.total_tokens==3

def test_gemini():
    p=GeminiProvider(api_key="x",transport=FakeTransport(
        {"candidates":[{"finishReason":"STOP","content":{"parts":[{"text":"{\"prediction\":10}"}]}}],
         "usageMetadata":{"promptTokenCount":2,"candidatesTokenCount":1,"totalTokenCount":3}}),
         clock=iter((1.0,1.2)).__next__)
    assert p.generate(request()).finish_reason=="STOP"

def test_manual_bom(tmp_path):
    path=tmp_path/"r.jsonl"
    path.write_text('{"case_id":"C1","text":"{\\\"prediction\\\":12}"}\n',encoding="utf-8-sig")
    p=ManualResponseProvider(path)
    assert p.generate(ModelRequest("x","m",metadata={"case_id":"C1"})).provider=="manual"

def test_bridge():
    class P:
        name="p"; capabilities=ProviderCapabilities()
        def generate(self,r): return ProviderResponse("p",r.model,'{"prediction":6,"confidence":80}',0.1)
    case=BatchCase(0,"C",1,8,hashlib.sha256(b"x").hexdigest(),
                   {"prompt":"Predict.","actual_value":6})
    result=ProviderExecutor(P(),lambda c: payload_prompt_builder(c,default_model="m"))(case)
    assert result.is_correct is True and result.confidence==80

def test_registry():
    assert default_registry().names()==("anthropic","gemini","http","manual","openai")
