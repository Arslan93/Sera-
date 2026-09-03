import React, { useState, useRef, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import AiStateOrb from '../AiStateOrb';
import { Send, Mic, RotateCcw } from 'lucide-react';
import { marked } from 'marked';

export default function ChatHubView() {
  const { 
    chatMessages, 
    streamingContent, 
    isGenerating, 
    sendMessage, 
    resetSession, 
    activeTool, 
    setAiState,
    showToast 
  } = useApp();

  const [inputVal, setInputVal] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [chatMessages, streamingContent]);

  function handleSend() {
    if (!inputVal.trim() || isGenerating) return;
    sendMessage(inputVal);
    setInputVal('');
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  async function handleMicRecord() {
    setIsRecording(true);
    setAiState('listening');
    try {
      const res = await fetch('/api/voice/listen', { method: 'POST' });
      const data = await res.json();
      if (data.status === 'success' && data.transcription) {
        setInputVal(data.transcription);
        sendMessage(data.transcription);
      } else {
        setAiState('idle');
      }
    } catch (e) {
      setAiState('idle');
      showToast('Mic error: ' + e.message, 'error');
    } finally {
      setIsRecording(false);
    }
  }

  return (
    <div className="view-panel flex-1 flex flex-col min-h-0 bg-[#F8FAFC]">
      {/* Agentic State Header */}
      <div className="flex-shrink-0 bg-white border-b border-slate-200 px-5 py-2.5 flex items-center justify-between shadow-sm">
        <AiStateOrb size="hero" />
        <button 
          onClick={resetSession}
          className="btn-secondary py-1 px-2.5 flex items-center gap-1 text-[11px]"
          title="Reset conversation"
        >
          <RotateCcw className="w-3 h-3" />
          <span>Clear Session</span>
        </button>
      </div>

      {/* Messages Stream */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-5 space-y-4">
        <div className="space-y-4 max-w-4xl mx-auto">
          {chatMessages.length === 0 && !streamingContent && (
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center text-white text-xs font-mono font-bold flex-shrink-0 mt-0.5 shadow-sm">
                S
              </div>
              <div className="chat-bubble-ai text-[13.5px] text-slate-700">
                <p className="font-semibold text-slate-900 mb-1">Session initialized.</p>
                Ready for coding assistance, study recall quizzes, CRM pipeline updates, or desktop tasks.
              </div>
            </div>
          )}

          {chatMessages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'items-start gap-3'}`}>
              {msg.role !== 'user' && (
                <div className="w-8 h-8 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center text-white text-xs font-mono font-bold flex-shrink-0 mt-0.5 shadow-sm">
                  S
                </div>
              )}
              {msg.role === 'user' ? (
                <div className="chat-bubble-user">{msg.content}</div>
              ) : (
                <div 
                  className="chat-bubble-ai prose-sera flex-1 overflow-x-auto text-[13.5px]"
                  dangerouslySetInnerHTML={{ __html: marked.parse(msg.content || '') }}
                />
              )}
            </div>
          ))}

          {/* Real-time Streaming Token Bubble */}
          {streamingContent && (
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center text-white text-xs font-mono font-bold flex-shrink-0 mt-0.5 shadow-sm">
                S
              </div>
              <div 
                className="chat-bubble-ai prose-sera flex-1 overflow-x-auto text-[13.5px]"
                dangerouslySetInnerHTML={{ __html: marked.parse(streamingContent) }}
              />
            </div>
          )}

          {/* Active Tool Calling Indicator */}
          {isGenerating && activeTool && (
            <div className="max-w-md mx-auto flex items-center gap-2.5 p-3 rounded-lg bg-white border border-purple-200 shadow-sm text-xs">
              <span className="w-2.5 h-2.5 rounded-full bg-purple-500 agentic-live"></span>
              <span className="font-mono text-purple-900 text-xs font-medium">
                Executing tool: {activeTool}...
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Pinned Input Dock */}
      <div className="flex-shrink-0 bg-white border-t border-slate-200/80 p-3.5 shadow-sm">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-2">
            <button 
              onClick={handleMicRecord}
              disabled={isRecording}
              className="btn-secondary p-2.5 flex items-center justify-center text-slate-600 hover:text-slate-900"
              title="Speak into microphone"
            >
              <Mic className={`w-4 h-4 ${isRecording ? 'text-rose-600 animate-pulse' : ''}`} />
            </button>
            <input 
              ref={inputRef}
              type="text" 
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask SERA, debug code, inspect system, or execute desktop tasks..." 
              className="studio-well flex-1 px-3.5 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-400 bg-white shadow-sm font-medium"
            />
            <button 
              onClick={handleSend}
              disabled={isGenerating || !inputVal.trim()}
              className="btn-primary flex items-center gap-1.5 px-4 py-2.5 font-semibold disabled:opacity-50"
            >
              <Send className="w-3.5 h-3.5" />
              <span>{isGenerating ? 'Thinking...' : 'Send'}</span>
            </button>
          </div>
          <div className="flex items-center justify-between text-[11px] text-slate-400 font-sans mt-2 px-1">
            <span>Agentic loop with self-debugging, PC control & skill plugins</span>
            <span className="font-mono text-[10.5px]">Press Enter</span>
          </div>
        </div>
      </div>
    </div>
  );
}
