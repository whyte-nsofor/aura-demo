import os
import json

PACKAGE_JSON = """{
  "name": "aura-frontend",
  "private": true,
  "version": "6.4.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@huggingface/transformers": "^3.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.17",
    "postcss": "^8.4.35",
    "tailwindcss": "^3.4.1",
    "vite": "^5.1.4"
  }
}"""

VITE_CONFIG = """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/v1': 'http://localhost:8000'
    }
  },
  build: {
    outDir: '../dist',
    emptyOutDir: true
  },
  publicDir: 'public'
});"""

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>AURA Enterprise AI Stack</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-neutral-950 text-neutral-100">
  <div id="root"></div>
  <script type="module" src="/src/main.jsx"></script>
</body>
</html>"""

MAIN_JSX = """// Copyright (c) 2025-2026 Whyte Chikwendu Nsofor. All rights reserved.
import React from 'react';
import ReactDOM from 'react-dom/client';
import AURAInterface from './AURAInterface.jsx';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AURAInterface />
  </React.StrictMode>
);"""

WHISPER_WORKER_JS = """// Copyright (c) 2025-2026 Whyte Chikwendu Nsofor. All rights reserved.
import { pipeline, env } from '@huggingface/transformers';

env.useWasmCache = true;

class WhisperPipeline {
  static instance = null;
  static model = 'onnx-community/whisper-tiny.en';

  static async getInstance(progress_callback = null) {
    if (this.instance === null) {
      this.instance = await pipeline('automatic-speech-recognition', this.model, {
        device: 'webgpu',
        dtype: 'fp32',
        progress_callback,
      });
    }
    return this.instance;
  }
}

self.addEventListener('message', async (event) => {
  const { type, audio } = event.data;

  if (type === 'LOAD') {
    try {
      await WhisperPipeline.getInstance((progress) => {
        self.postMessage({ type: 'PROGRESS', progress });
      });
      self.postMessage({ type: 'READY' });
    } catch (error) {
      self.postMessage({ type: 'ERROR', error: error.message });
    }
  }

  if (type === 'TRANSCRIBE') {
    try {
      const transcriber = await WhisperPipeline.getInstance();
      const output = await transcriber(audio, {
        chunk_length_s: 30,
        stride_length_s: 5,
        language: 'english',
        task: 'transcribe',
      });
      self.postMessage({ type: 'COMPLETE', text: output.text });
    } catch (error) {
      self.postMessage({ type: 'ERROR', error: error.message });
    }
  }
});"""

AUDIO_UTILS_JS = """// Copyright (c) 2025-2026 Whyte Chikwendu Nsofor. All rights reserved.
export async function processAudioBlob(audioBlob) {
  const arrayBuffer = await audioBlob.arrayBuffer();
  const audioContext = new (window.AudioContext || window.webkitAudioContext)({
    sampleRate: 16000,
  });

  const audioBuffer = await audioContext.decodeAudioBuffer(arrayBuffer);
  const pcmData = audioBuffer.getChannelData(0);
  await audioContext.close();
  
  return pcmData;
}"""

AURA_INTERFACE_JSX = """// Copyright (c) 2025-2026 Whyte Chikwendu Nsofor. All rights reserved.
import React, { useState, useEffect, useRef } from 'react';
import { processAudioBlob } from './audioUtils';

export default function AURAInterface() {
  const [activeTab, setActiveTab] = useState('memory');
  const [zkProof, setZkProof] = useState('mock_proof');
  
  // Memory tab
  const [ingestFactId, setIngestFactId] = useState('');
  const [ingestEntity, setIngestEntity] = useState('');
  const [ingestKey, setIngestKey] = useState('');
  const [ingestValue, setIngestValue] = useState('');
  const [ingestSalt, setIngestSalt] = useState('secret_salt_123');
  const [ingestResult, setIngestResult] = useState(null);
  const [ingestError, setIngestError] = useState('');

  const [searchQuery, setSearchQuery] = useState('');
  const [searchTopK, setSearchTopK] = useState(5);
  const [searchResults, setSearchResults] = useState([]);
  const [searchError, setSearchError] = useState('');

  const [eraseFactId, setEraseFactId] = useState('');
  const [eraseEntity, setEraseEntity] = useState('');
  const [eraseSalt, setEraseSalt] = useState('secret_salt_123');
  const [eraseResult, setEraseResult] = useState(null);
  const [eraseError, setEraseError] = useState('');

  // Voice tab
  const [voiceText, setVoiceText] = useState('');
  const [isReady, setIsReady] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const workerRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // UI, MCP, DAG, Security tabs
  const [prompt, setPrompt] = useState('show memory dashboard');
  const [uiSchema, setUiSchema] = useState(null);
  const [mcpData, setMcpData] = useState(null);
  const [dagResults, setDagResults] = useState(null);
  const [runtimeResults, setRuntimeResults] = useState(null);
  const [runtimeAgentName, setRuntimeAgentName] = useState('test_agent');
  const [runtimeAction, setRuntimeAction] = useState('Check telemetry');
  const [runtimeTool, setRuntimeTool] = useState('fetch_telemetry');
  const [runtimePayload, setRuntimePayload] = useState('{"sensor_id": "main"}');
  const [runtimeAllowedTools, setRuntimeAllowedTools] = useState('["fetch_telemetry"]');
  const [runtimeMaxLevel, setRuntimeMaxLevel] = useState('LOW');

  const textToEmbedding = (text) => {
    const vec = new Array(384).fill(0);
    for (let i = 0; i < text.length; i++) {
      vec[i % 384] += text.charCodeAt(i) / 255;
    }
    return vec.map(v => Number(v.toFixed(6)));
  };

  const handleIngest = async (e) => {
    e.preventDefault();
    setIngestError('');
    setIngestResult(null);
    try {
      const payload = {
        fact_id: ingestFactId || `fact_${Date.now()}`,
        entity_did: ingestEntity || 'did:aura:default',
        fact_key: ingestKey,
        fact_value: ingestValue,
        embedding: textToEmbedding(ingestKey + ' ' + ingestValue),
        user_secret_salt: ingestSalt
      };
      const res = await fetch('/v1/memory/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Aura-ZK-Proof': zkProof },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Ingest failed');
      setIngestResult(data);
    } catch (err) {
      setIngestError(err.message);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    setSearchError('');
    setSearchResults([]);
    try {
      const payload = { query_embedding: textToEmbedding(searchQuery), top_k: searchTopK };
      const res = await fetch('/v1/memory/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Aura-ZK-Proof': zkProof },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Search failed');
      setSearchResults(data.results || []);
    } catch (err) {
      setSearchError(err.message);
    }
  };

  const handleErase = async (e) => {
    e.preventDefault();
    setEraseError('');
    setEraseResult(null);
    try {
      const payload = { fact_id: eraseFactId, entity_did: eraseEntity, user_secret_salt: eraseSalt };
      const res = await fetch('/v1/memory/erase', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json', 'X-Aura-ZK-Proof': zkProof },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Erase failed');
      setEraseResult(data);
    } catch (err) {
      setEraseError(err.message);
    }
  };

  useEffect(() => {
    workerRef.current = new Worker('/whisper.worker.js', { type: 'module' });
    workerRef.current.onmessage = (e) => {
      const { type, text, error } = e.data;
      if (type === 'READY') setIsReady(true);
      if (type === 'COMPLETE') { setIsProcessing(false); setVoiceText(text); }
      if (type === 'ERROR') { console.error("Worker Error:", error); setIsProcessing(false); }
    };
    workerRef.current.postMessage({ type: 'LOAD' });
    return () => workerRef.current?.terminate();
  }, []);

  const handleStartRecord = async () => {
    audioChunksRef.current = [];
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorderRef.current = new MediaRecorder(stream);
    mediaRecorderRef.current.ondataavailable = (e) => audioChunksRef.current.push(e.data);
    mediaRecorderRef.current.onstop = async () => {
      setIsProcessing(true);
      const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
      const pcmData = await processAudioBlob(audioBlob);
      workerRef.current.postMessage({ type: 'TRANSCRIBE', audio: pcmData });
      stream.getTracks().forEach(t => t.stop());
    };
    mediaRecorderRef.current.start();
    setIsRecording(true);
  };

  const handleStopRecord = () => {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
  };

  const triggerGenerativeUI = async () => {
    const res = await fetch('/v1/ai/generate_ui', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt })
    });
    const data = await res.json();
    setUiSchema(data);
  };

  const fetchMCPApp = async () => {
    const res = await fetch('/v1/mcp/app', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ app_name: 'memory_browser' })
    });
    const data = await res.json();
    setMcpData(data.ui);
  };

  const executeDAGWorkflow = async () => {
    const payload = {
      nodes: [
        { id: "A", type: "supervisor", config: { sub_tasks: ["research", "code"] } },
        { id: "B", type: "agent", config: { agent_type: "researcher", task: "research", shared_memory_updates: { topic: "AI" } } },
        { id: "C", type: "agent", config: { agent_type: "coder", task: "code", shared_memory_updates: { code: "print" } } }
      ],
      edges: [
        { source: "A", target: "B" },
        { source: "B", target: "C" }
      ]
    };
    const res = await fetch('/v1/agent/workflow', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    setDagResults(data);
  };

  const executeRuntime = async () => {
    try {
      const payload = {
        agent_name: runtimeAgentName,
        proposed_action: runtimeAction,
        tool_name: runtimeTool,
        tool_payload: JSON.parse(runtimePayload),
        allowed_tools: JSON.parse(runtimeAllowedTools),
        max_security_level: runtimeMaxLevel
      };
      const res = await fetch('/v1/runtime/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Aura-ZK-Proof': zkProof },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      setRuntimeResults(data);
    } catch (e) {
      setRuntimeResults({ error: e.message });
    }
  };

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 p-8 font-sans">
      <header className="mb-8 border-b border-neutral-800 pb-4 flex justify-between items-center">
        <h1 className="text-2xl font-bold tracking-tight text-emerald-400">AURA Unified System Stack</h1>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-xs text-neutral-500">ZK Proof:</span>
            <input type="text" value={zkProof} onChange={(e) => setZkProof(e.target.value)} className="bg-neutral-900 border border-neutral-700 rounded px-2 py-1 text-xs w-32" />
          </div>
          <div className="flex gap-2">
            {['memory','voice','ui','mcp','dag','security'].map(tab => (
              <button key={tab} onClick={() => setActiveTab(tab)} className={`px-4 py-1.5 rounded-md text-xs font-semibold capitalize transition ${activeTab===tab?'bg-emerald-600 text-white':'bg-neutral-900 text-neutral-400 hover:bg-neutral-800'}`}>
                {tab}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Memory Tab */}
      {activeTab === 'memory' && (
        <div className="max-w-4xl mx-auto space-y-8">
          <section className="bg-neutral-900 p-6 rounded-xl border border-neutral-800">
            <h2 className="text-lg font-semibold mb-4">Ingest Fact</h2>
            <form onSubmit={handleIngest} className="grid grid-cols-2 gap-3">
              <input type="text" placeholder="Fact ID" value={ingestFactId} onChange={e=>setIngestFactId(e.target.value)} className="bg-neutral-950 px-3 py-2 rounded border border-neutral-700 text-sm" />
              <input type="text" placeholder="Entity DID" value={ingestEntity} onChange={e=>setIngestEntity(e.target.value)} className="bg-neutral-950 px-3 py-2 rounded border border-neutral-700 text-sm" />
              <input type="text" placeholder="Key" value={ingestKey} onChange={e=>setIngestKey(e.target.value)} className="bg-neutral-950 px-3 py-2 rounded border border-neutral-700 text-sm" />
              <input type="text" placeholder="Value" value={ingestValue} onChange={e=>setIngestValue(e.target.value)} className="bg-neutral-950 px-3 py-2 rounded border border-neutral-700 text-sm" />
              <input type="text" placeholder="Secret Salt" value={ingestSalt} onChange={e=>setIngestSalt(e.target.value)} className="bg-neutral-950 px-3 py-2 rounded border border-neutral-700 text-sm col-span-2" />
              <button type="submit" className="col-span-2 bg-emerald-600 hover:bg-emerald-500 text-white py-2 rounded font-semibold">Ingest</button>
            </form>
            {ingestError && <div className="mt-2 text-rose-400 text-sm">{ingestError}</div>}
            {ingestResult && <div className="mt-2 text-emerald-400 text-xs"><pre>{JSON.stringify(ingestResult, null, 2)}</pre></div>}
          </section>

          <section className="bg-neutral-900 p-6 rounded-xl border border-neutral-800">
            <h2 className="text-lg font-semibold mb-4">Search Memory</h2>
            <form onSubmit={handleSearch} className="flex gap-3">
              <input type="text" placeholder="Search query..." value={searchQuery} onChange={e=>setSearchQuery(e.target.value)} className="flex-1 bg-neutral-950 px-3 py-2 rounded border border-neutral-700 text-sm" />
              <input type="number" placeholder="Top K" value={searchTopK} onChange={e=>setSearchTopK(parseInt(e.target.value)||5)} className="w-20 bg-neutral-950 px-3 py-2 rounded border border-neutral-700 text-sm" />
              <button type="submit" className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded font-semibold">Search</button>
            </form>
            {searchError && <div className="mt-2 text-rose-400 text-sm">{searchError}</div>}
            {searchResults.length > 0 && (
              <div className="mt-4">
                <table className="w-full text-sm">
                  <thead className="text-neutral-400 border-b border-neutral-700">
                    <tr><th className="text-left py-1">Fact ID</th><th>Key</th><th>Value</th><th>Score</th></tr>
                  </thead>
                  <tbody>
                    {searchResults.map((r,i) => (
                      <tr key={i} className="border-b border-neutral-800">
                        <td className="py-1 text-emerald-400">{r.fact_id}</td>
                        <td>{r.fact_key}</td>
                        <td>{r.fact_value}</td>
                        <td>{r.score}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="bg-neutral-900 p-6 rounded-xl border border-neutral-800">
            <h2 className="text-lg font-semibold mb-4">Erase Fact</h2>
            <form onSubmit={handleErase} className="grid grid-cols-3 gap-3">
              <input type="text" placeholder="Fact ID" value={eraseFactId} onChange={e=>setEraseFactId(e.target.value)} className="bg-neutral-950 px-3 py-2 rounded border border-neutral-700 text-sm" />
              <input type="text" placeholder="Entity DID" value={eraseEntity} onChange={e=>setEraseEntity(e.target.value)} className="bg-neutral-950 px-3 py-2 rounded border border-neutral-700 text-sm" />
              <input type="text" placeholder="Secret Salt" value={eraseSalt} onChange={e=>setEraseSalt(e.target.value)} className="bg-neutral-950 px-3 py-2 rounded border border-neutral-700 text-sm" />
              <button type="submit" className="col-span-3 bg-rose-600 hover:bg-rose-500 text-white py-2 rounded font-semibold">Erase & Prove</button>
            </form>
            {eraseError && <div className="mt-2 text-rose-400 text-sm">{eraseError}</div>}
            {eraseResult && <div className="mt-2 text-emerald-400 text-xs"><pre>{JSON.stringify(eraseResult, null, 2)}</pre></div>}
          </section>
        </div>
      )}

      {/* Voice Tab */}
      {activeTab === 'voice' && (
        <section className="max-w-xl mx-auto bg-neutral-900 p-6 rounded-xl border border-neutral-800">
          <h2 className="text-lg font-semibold mb-4">Local WebGPU Speech Engine</h2>
          <div className="flex items-center gap-4 mb-6">
            <button onClick={isRecording ? handleStopRecord : handleStartRecord} disabled={!isReady || isProcessing} className={`px-6 py-2.5 rounded-lg text-sm font-semibold transition ${isRecording?'bg-rose-600 animate-pulse text-white':'bg-emerald-600 hover:bg-emerald-500 text-white'} ${(!isReady||isProcessing)&&'opacity-50 cursor-not-allowed'}`}>
              {!isReady ? 'Loading Pipeline...' : isProcessing ? 'Transcribing (WebGPU)...' : isRecording ? 'Stop Recording' : 'Start Recording'}
            </button>
          </div>
          <div className="bg-neutral-950 p-4 rounded-lg border border-neutral-800">
            <p className="text-xs text-neutral-500 mb-1">Transcription Output:</p>
            <p className="text-sm">{voiceText || 'No active voice input transcribed.'}</p>
          </div>
        </section>
      )}

      {/* UI Tab */}
      {activeTab === 'ui' && (
        <section className="max-w-2xl mx-auto bg-neutral-900 p-6 rounded-xl border border-neutral-800">
          <h2 className="text-lg font-semibold mb-4">Dynamic UI Schema Renderer</h2>
          <div className="flex gap-2 mb-6">
            <input type="text" value={prompt} onChange={(e)=>setPrompt(e.target.value)} className="flex-1 bg-neutral-950 px-3 py-2 text-sm rounded-lg border border-neutral-800" />
            <button onClick={triggerGenerativeUI} className="bg-emerald-600 px-4 py-2 rounded-lg text-sm font-semibold">Generate</button>
          </div>
          {uiSchema && (
            <div className="grid grid-cols-2 gap-4">
              {uiSchema.components.map((c,i) => (
                <div key={i} className="bg-neutral-950 p-4 rounded-lg border border-neutral-800">
                  <p className="text-xs text-neutral-500">{c.title || c.type}</p>
                  <p className="text-lg font-bold text-emerald-400">{c.value || JSON.stringify(c.data)}</p>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {/* MCP Tab */}
      {activeTab === 'mcp' && (
        <section className="max-w-xl mx-auto bg-neutral-900 p-6 rounded-xl border border-neutral-800">
          <h2 className="text-lg font-semibold mb-4">MCP Interactive Widget Sandbox</h2>
          <button onClick={fetchMCPApp} className="bg-emerald-600 px-4 py-2 rounded-lg text-sm font-semibold mb-4">Load Memory Browser</button>
          {mcpData && (
            <div className="bg-neutral-950 p-4 rounded-lg border border-neutral-800 space-y-2">
              {mcpData.components[0].items.map((item,idx) => (
                <div key={idx} className="flex justify-between items-center bg-neutral-900 p-2.5 rounded border border-neutral-800 text-sm">
                  <span>{item.key}</span>
                  <span className="font-mono text-xs text-emerald-400">{item.value}</span>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {/* DAG Tab */}
      {activeTab === 'dag' && (
        <section className="max-w-xl mx-auto bg-neutral-900 p-6 rounded-xl border border-neutral-800">
          <h2 className="text-lg font-semibold mb-4">Topological DAG Execution Loop</h2>
          <button onClick={executeDAGWorkflow} className="bg-emerald-600 px-4 py-2 rounded-lg text-sm font-semibold mb-4">Run DAG Workflow</button>
          {dagResults && (
            <div className="bg-neutral-950 p-4 rounded-lg border border-neutral-800">
              <p className="text-xs text-neutral-500 mb-2">Execution Order: {dagResults.execution_order.join(' → ')}</p>
              <pre className="text-xs text-emerald-400 overflow-x-auto">{JSON.stringify(dagResults.node_outputs, null, 2)}</pre>
            </div>
          )}
        </section>
      )}

      {/* Security Tab */}
      {activeTab === 'security' && (
        <section className="max-w-3xl mx-auto bg-neutral-900 p-6 rounded-xl border border-neutral-800">
          <h2 className="text-lg font-semibold mb-4">Zero Trust Runtime</h2>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <input type="text" placeholder="Agent Name" value={runtimeAgentName} onChange={e=>setRuntimeAgentName(e.target.value)} className="bg-neutral-950 px-3 py-2 rounded border border-neutral-700 text-sm" />
              <input type="text" placeholder="Action" value={runtimeAction} onChange={e=>setRuntimeAction(e.target.value)} className="bg-neutral-950 px-3 py-2 rounded border border-neutral-700 text-sm" />
              <input type="text" placeholder="Tool Name" value={runtimeTool} onChange={e=>setRuntimeTool(e.target.value)} className="bg-neutral-950 px-3 py-2 rounded border border-neutral-700 text-sm" />
              <input type="text" placeholder='Tool Payload (JSON)' value={runtimePayload} onChange={e=>setRuntimePayload(e.target.value)} className="bg-neutral-950 px-3 py-2 rounded border border-neutral-700 text-sm" />
              <input type="text" placeholder='Allowed Tools (JSON)' value={runtimeAllowedTools} onChange={e=>setRuntimeAllowedTools(e.target.value)} className="bg-neutral-950 px-3 py-2 rounded border border-neutral-700 text-sm" />
              <select value={runtimeMaxLevel} onChange={e=>setRuntimeMaxLevel(e.target.value)} className="bg-neutral-950 px-3 py-2 rounded border border-neutral-700 text-sm">
                <option value="LOW">LOW</option>
                <option value="MEDIUM">MEDIUM</option>
                <option value="HIGH">HIGH</option>
                <option value="CRITICAL">CRITICAL</option>
              </select>
            </div>
            <button onClick={executeRuntime} className="bg-emerald-600 px-4 py-2 rounded-lg text-sm font-semibold">Execute Step</button>
            {runtimeResults && (
              <div className="mt-2 bg-neutral-950 p-4 rounded-lg border border-neutral-800">
                <pre className="text-xs text-emerald-400 overflow-x-auto">{JSON.stringify(runtimeResults, null, 2)}</pre>
              </div>
            )}
          </div>
        </section>
      )}
    </div>
  );
}"""

def main():
    base_dir = "frontend"
    src_dir = os.path.join(base_dir, "src")
    public_dir = os.path.join(base_dir, "public")
    os.makedirs(src_dir, exist_ok=True)
    os.makedirs(public_dir, exist_ok=True)

    files = {
        os.path.join(base_dir, "package.json"): PACKAGE_JSON,
        os.path.join(base_dir, "vite.config.js"): VITE_CONFIG,
        os.path.join(base_dir, "index.html"): INDEX_HTML,
        os.path.join(src_dir, "main.jsx"): MAIN_JSX,
        os.path.join(src_dir, "audioUtils.js"): AUDIO_UTILS_JS,
        os.path.join(src_dir, "AURAInterface.jsx"): AURA_INTERFACE_JSX,
        os.path.join(public_dir, "whisper.worker.js"): WHISPER_WORKER_JS,
    }
    for path, content in files.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    print("Frontend source files generated.")

if __name__ == "__main__":
    main()
