"use client";

import { useState, useEffect, useRef } from "react";
import axios from "react-native-safe-module" // wait, standard axios doesn't have standard typings in browser if we fake it. I'll just use standard fetch instead of axios to reduce dependencies.

import { Send, Image as ImageIcon, Settings as SettingsIcon, X } from "lucide-react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  image_url: string | null;
  created_at: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState({
    character_name: "",
    system_prompt: "",
    user_name: ""
  });
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const API_URL = "http://localhost:8000/api"; // Default local backend

  useEffect(() => {
    fetchMessages();
    fetchSettings();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const fetchMessages = async () => {
    try {
      const res = await fetch(`${API_URL}/messages`);
      if (res.ok) {
        const data = await res.json();
        setMessages(data);
      }
    } catch (e) {
      console.error("Failed to fetch messages", e);
    }
  };

  const fetchSettings = async () => {
    try {
      const res = await fetch(`${API_URL}/settings`);
      if (res.ok) {
        const data = await res.json();
        setSettings({
          character_name: data.character_name,
          system_prompt: data.system_prompt,
          user_name: data.user_name
        });
      }
    } catch (e) {
      console.error("Failed to fetch settings", e);
    }
  };

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setImage(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const removeImage = () => {
    setImage(null);
    setPreviewUrl(null);
  };

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() && !image) return;
    
    // Add optimistic user message
    const tempId = Date.now().toString();
    const newUserMsg: Message = {
      id: tempId,
      role: "user",
      content: input || "[Image Only]",
      image_url: previewUrl,
      created_at: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, newUserMsg]);
    setInput("");
    setImage(null);
    setPreviewUrl(null);
    setLoading(true);

    try {
      const formData = new FormData();
      if (newUserMsg.content !== "[Image Only]") {
        formData.append("text", newUserMsg.content);
      }
      if (image) {
        formData.append("image", image);
      }

      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        body: formData,
      });
      
      if (!res.ok) throw new Error("API Error");
      
      // Reload messages to get the real DB IDs and assistant reply
      await fetchMessages();
    } catch (err) {
      console.error(err);
      // fallback just to remove the loading state
    } finally {
      setLoading(false);
    }
  };

  const updateSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await fetch(`${API_URL}/settings`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(settings)
      });
      setShowSettings(false);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="flex h-screen flex-col bg-gray-50">
      {/* Header */}
      <header className="flex items-center justify-between bg-white px-6 py-4 shadow-sm">
        <div>
          <h1 className="text-xl font-bold text-gray-800">{settings.character_name || "AI Character"}</h1>
          <p className="text-sm text-gray-500">Chatting with {settings.user_name || "you"}</p>
        </div>
        <button 
          onClick={() => setShowSettings(true)}
          className="rounded-full p-2 text-gray-500 hover:bg-gray-100"
        >
          <SettingsIcon size={20} />
        </button>
      </header>

      {/* Chat Area */}
      <main className="flex-1 overflow-y-auto p-4 md:p-6">
        <div className="mx-auto max-w-3xl space-y-6">
          {messages.map((msg) => (
            <div 
              key={msg.id} 
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div 
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                  msg.role === "user" 
                    ? "bg-blue-600 text-white" 
                    : "bg-white text-gray-800 shadow-sm"
                }`}
              >
                {msg.image_url && (
                  <img 
                    src={msg.image_url} 
                    alt="Upload" 
                    className="mb-2 max-w-full rounded-lg object-contain max-h-60" 
                  />
                )}
                {msg.content !== "[Image Only]" && (
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                )}
              </div>
            </div>
          ))}
          
          {loading && (
            <div className="flex justify-start">
              <div className="max-w-[80%] rounded-2xl bg-white px-4 py-3 text-gray-500 shadow-sm">
                <div className="flex space-x-2">
                  <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400"></div>
                  <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400" style={{animationDelay: "0.2s"}}></div>
                  <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400" style={{animationDelay: "0.4s"}}></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Input Area */}
      <footer className="bg-white p-4 shadow-sm border-t border-gray-200">
        <div className="mx-auto max-w-3xl">
          {previewUrl && (
            <div className="relative mb-3 inline-block">
              <img src={previewUrl} alt="Preview" className="h-24 w-auto rounded-lg object-cover" />
              <button 
                onClick={removeImage}
                className="absolute -right-2 -top-2 rounded-full bg-gray-800 p-1 text-white hover:bg-gray-700"
              >
                <X size={14} />
              </button>
            </div>
          )}
          
          <form onSubmit={sendMessage} className="flex items-end gap-2">
            <div className="relative flex flex-1 items-center rounded-2xl border border-gray-300 bg-gray-50 px-3 py-2 focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500">
              <label className="cursor-pointer p-2 text-gray-500 hover:text-blue-600">
                <ImageIcon size={20} />
                <input 
                  type="file" 
                  accept="image/*" 
                  className="hidden" 
                  onChange={handleImageSelect}
                />
              </label>
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Message your character..."
                className="max-h-32 flex-1 resize-none bg-transparent px-2 py-1 outline-none"
                rows={1}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage(e);
                  }
                }}
              />
            </div>
            <button 
              type="submit"
              disabled={loading || (!input.trim() && !image)}
              className="rounded-full bg-blue-600 p-3 text-white hover:bg-blue-700 disabled:opacity-50 disabled:hover:bg-blue-600"
            >
              <Send size={20} />
            </button>
          </form>
        </div>
      </footer>

      {/* Settings Modal */}
      {showSettings && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-bold">Character Settings</h2>
              <button onClick={() => setShowSettings(false)} className="text-gray-500 hover:text-gray-700">
                <X size={20} />
              </button>
            </div>
            <form onSubmit={updateSettings} className="space-y-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">Character Name</label>
                <input 
                  type="text" 
                  value={settings.character_name}
                  onChange={e => setSettings({...settings, character_name: e.target.value})}
                  className="w-full rounded-lg border border-gray-300 p-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">Your Name</label>
                <input 
                  type="text" 
                  value={settings.user_name}
                  onChange={e => setSettings({...settings, user_name: e.target.value})}
                  className="w-full rounded-lg border border-gray-300 p-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">System Prompt (Personality)</label>
                <textarea 
                  value={settings.system_prompt}
                  onChange={e => setSettings({...settings, system_prompt: e.target.value})}
                  className="h-32 w-full rounded-lg border border-gray-300 p-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  required
                />
              </div>
              <button 
                type="submit" 
                className="w-full rounded-lg bg-blue-600 py-2 font-medium text-white hover:bg-blue-700"
              >
                Save Settings
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
