"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "@/components/ui/accordion";
import { Loader2, Download, PlaySquare, AlertCircle, RefreshCw } from "lucide-react";
import { toast } from "sonner";

interface VideoFormat {
  format_id: string;
  resolution?: string;
  ext: string;
  filesize?: number;
}

interface VideoInfo {
  title: string;
  thumbnail?: string;
  formats: VideoFormat[];
  original_url: string;
}

interface Task {
  id: string;
  url: string;
  title?: string;
  status: string;
  format_id?: string;
  error_msg?: string;
  created_at: string;
  local_url?: string;
}

interface CookieStatus {
  bilibili: boolean;
  douyin: boolean;
  youtube: boolean;
}

// Use relative path — Nginx inside the container proxies /api/* → FastAPI.
// This works for local dev (via next.config rewrites) and production (via Nginx).
const API_URL = "/api/v1";

export default function Home() {
  const [url, setUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [videoInfo, setVideoInfo] = useState<VideoInfo | null>(null);
  const [selectedFormat, setSelectedFormat] = useState("best");
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isFetchingTasks, setIsFetchingTasks] = useState(false);
  const [cookieStatus, setCookieStatus] = useState<CookieStatus | null>(null);

  const fetchTasks = useCallback(async () => {
    setIsFetchingTasks(true);
    try {
      const response = await fetch(`${API_URL}/video/tasks`);
      if (response.ok) {
        const data = await response.json();
        setTasks(data);
      }
    } catch {
      // Silently suppress network errors during background polling
    } finally {
      setTimeout(() => setIsFetchingTasks(false), 500);
    }
  }, []);

  const fetchCookieStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/video/cookies/status`);
      if (response.ok) {
        setCookieStatus(await response.json());
      }
    } catch { }
  }, []);

  useEffect(() => {
    fetchCookieStatus();
    fetchTasks();
    const interval = setInterval(fetchTasks, 3000);
    return () => clearInterval(interval);
  }, [fetchTasks, fetchCookieStatus]);

  const parseVideo = async () => {
    if (!url) return;
    setIsLoading(true);
    setErrorMsg("");
    setVideoInfo(null);

    try {
      const response = await fetch(`${API_URL}/video/parse`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Failed to parse video.");
      setVideoInfo({ ...data, original_url: url });
      setTimeout(() => {
        document.getElementById("result-section")?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsLoading(false);
    }
  };

  const downloadVideo = async () => {
    if (!videoInfo) return;
    setIsDownloading(true);
    setErrorMsg("");

    try {
      const response = await fetch(`${API_URL}/video/download`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: videoInfo.original_url,
          format_id: selectedFormat,
        })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Failed to start download task");
      toast.success(`✅ Download queued! ID: ${data.task_id.split("-")[0]}`);
      fetchTasks();
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsDownloading(false);
    }
  };

  const formatBytes = (bytes?: number) => {
    if (!bytes) return "Unknown";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "COMPLETED": return "bg-emerald-500/20 text-emerald-400 border-none";
      case "FAILED": return "bg-red-500/20 text-red-400 border-none";
      case "DOWNLOADING": return "bg-amber-500/20 text-amber-400 border-none";
      default: return "bg-slate-500/20 text-slate-400 border-none";
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden bg-slate-950 text-slate-50 font-sans selection:bg-blue-500/30">
      <div className="blob blob-1"></div>
      <div className="blob blob-2"></div>

      <div className="max-w-4xl mx-auto p-4 sm:p-8 flex flex-col gap-8 relative z-10">
        {/* Header */}
        <div className="flex flex-col gap-4">
          <header className="glass-panel p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between shadow-lg shadow-black/20 gap-4">
            <div className="flex items-center gap-4">
              <PlaySquare className="w-8 h-8 text-blue-400" />
              <h1 className="text-2xl font-bold tracking-tight">Accio</h1>
              <Badge variant="secondary" className="bg-blue-500/20 text-blue-400 hover:bg-blue-500/30">
                Downloader
              </Badge>
            </div>

            {cookieStatus && (
              <div
                className="flex items-center gap-3 bg-slate-950/50 px-3 py-1.5 rounded-full border border-white/10 text-xs font-medium cursor-help"
                title="Green means the cookie is active in the container"
              >
                <span className="text-slate-500">Cookie Status:</span>
                <span className={`flex items-center gap-1.5 ${cookieStatus.bilibili ? 'text-emerald-400' : 'text-slate-600'}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${cookieStatus.bilibili ? 'bg-emerald-400' : 'bg-slate-700'}`}></span>
                  Bili
                </span>
                <span className={`flex items-center gap-1.5 ${cookieStatus.douyin ? 'text-emerald-400' : 'text-slate-600'}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${cookieStatus.douyin ? 'bg-emerald-400' : 'bg-slate-700'}`}></span>
                  Douyin
                </span>
                <span className={`flex items-center gap-1.5 ${cookieStatus.youtube ? 'text-emerald-400' : 'text-slate-600'}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${cookieStatus.youtube ? 'bg-emerald-400' : 'bg-slate-700'}`}></span>
                  YT
                </span>
              </div>
            )}
          </header>

          {/* Input Card */}
          <Card className="glass-panel border-white/10 text-slate-50 bg-slate-900/40 shadow-xl shadow-black/20">
            <CardHeader className="py-4">
              <CardTitle className="text-xl">Paste your video link</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-4 pb-4">
              <div className="flex flex-col sm:flex-row gap-4">
                <Input
                  type="url"
                  placeholder="https://www.bilibili.com/video/... or YouTube, TikTok, etc."
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  disabled={isLoading}
                  onKeyDown={(e) => e.key === "Enter" && parseVideo()}
                  className="bg-slate-950/50 border-white/10 text-white placeholder:text-slate-500 h-12 focus-visible:ring-blue-500"
                />
                <Button
                  onClick={parseVideo}
                  disabled={!url || isLoading}
                  className="h-12 px-8 bg-blue-600 hover:bg-blue-700 text-white font-semibold transition-all"
                >
                  {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Parse"}
                </Button>
              </div>

              {errorMsg && (
                <div className="flex items-center gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                  <AlertCircle className="w-5 h-5 flex-shrink-0" />
                  <p>{errorMsg}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <main className="flex flex-col gap-8">
          {/* Video Info + Download */}
          {videoInfo && (
            <div id="result-section" className="animate-in fade-in slide-in-from-bottom-4 duration-500">
              <Card className="glass-panel border-white/10 text-slate-50 bg-slate-900/40 overflow-hidden">
                <CardContent className="p-6">
                  <div className="grid grid-cols-1 sm:grid-cols-[280px_1fr] gap-8">
                    <div className="aspect-video bg-black/50 rounded-xl overflow-hidden border border-white/10 flex items-center justify-center">
                      {videoInfo.thumbnail ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img src={videoInfo.thumbnail} alt="Thumbnail" className="w-full h-full object-cover" />
                      ) : (
                        <p className="text-slate-500">No Thumbnail</p>
                      )}
                    </div>
                    <div className="flex flex-col gap-6">
                      <h3 className="text-xl font-semibold leading-snug line-clamp-3" title={videoInfo.title}>
                        {videoInfo.title}
                      </h3>

                      <div className="flex flex-col gap-2">
                        <label className="text-sm font-medium text-slate-400">Select Quality</label>
                        <Select value={selectedFormat} onValueChange={setSelectedFormat}>
                          <SelectTrigger className="w-full bg-slate-950/80 border-white/10 focus:ring-blue-500 h-11">
                            <SelectValue placeholder="Select quality..." />
                          </SelectTrigger>
                          <SelectContent className="bg-slate-900 border-white/10 text-slate-50">
                            <SelectItem value="best">Best Quality (Auto)</SelectItem>
                            {videoInfo.formats.map((fmt) => (
                              <SelectItem key={fmt.format_id} value={fmt.format_id}>
                                {fmt.resolution || "Audio"} ({fmt.ext}){fmt.filesize ? ` · ${formatBytes(fmt.filesize)}` : ""}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <Button
                        onClick={downloadVideo}
                        disabled={isDownloading}
                        className="h-12 bg-blue-600 hover:bg-blue-700 font-semibold text-base"
                      >
                        {isDownloading
                          ? <><Loader2 className="w-5 h-5 mr-2 animate-spin" />Queuing...</>
                          : <><Download className="w-5 h-5 mr-2" />Download to NAS</>
                        }
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Task Dashboard */}
          <Card className="glass-panel border-white/10 text-slate-50 bg-slate-900/40">
            <CardHeader className="flex flex-row items-center justify-between pb-4">
              <div>
                <CardTitle className="text-xl">Task Dashboard</CardTitle>
                <CardDescription className="text-slate-400">Monitor your active downloads</CardDescription>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={fetchTasks}
                disabled={isFetchingTasks}
                className="hover:bg-white/10 text-slate-300"
              >
                <RefreshCw className={`w-5 h-5 ${isFetchingTasks ? 'animate-spin' : ''}`} />
              </Button>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col gap-3">
                {tasks.length === 0 ? (
                  <div className="text-center p-8 bg-black/20 rounded-xl border border-white/5 text-slate-500 italic">
                    No download tasks yet.
                  </div>
                ) : (
                  <Accordion type="single" collapsible className="w-full flex flex-col gap-3">
                    {tasks.map(task => (
                      <AccordionItem key={task.id} value={task.id} className="bg-slate-950/40 border border-white/10 rounded-xl px-4 hover:bg-slate-950/60 transition-colors data-[state=open]:bg-slate-900/60">
                        <div className="flex flex-col sm:flex-row justify-between sm:items-center py-4 gap-4">
                          <div className="flex flex-col gap-1.5 overflow-hidden flex-1">
                            <span className="font-semibold truncate pr-4" title={task.title || task.url}>
                              {task.title || "Processing..."}
                            </span>
                            <div className="flex items-center gap-2 text-xs text-slate-400">
                              <span>ID: {task.id.split('-')[0]}</span>
                              <span className="opacity-50">•</span>
                              <span>{new Date(task.created_at).toLocaleString()}</span>
                            </div>
                            {task.error_msg && (
                              <div className="text-xs text-red-400 truncate mt-1">
                                ⚠ {task.error_msg}
                              </div>
                            )}
                          </div>
                          <div className="flex items-center gap-3 shrink-0">
                            <Badge className={getStatusColor(task.status)}>{task.status}</Badge>
                            {task.status === "COMPLETED" && task.local_url && (
                              <a
                                href={`${API_URL.replace('/api/v1', '')}${task.local_url}`}
                                download
                                onClick={(e) => e.stopPropagation()}
                                className="p-2 text-blue-400 hover:text-blue-300 hover:bg-blue-400/10 rounded-full transition-colors"
                                title="Download File"
                              >
                                <Download className="w-5 h-5" />
                              </a>
                            )}
                            <AccordionTrigger className="p-2 hover:bg-white/10 rounded-full [&>svg]:text-white data-[state=open]:rotate-180" />
                          </div>
                        </div>

                        <AccordionContent>
                          <div className="pt-2 pb-4 border-t border-white/10 flex flex-col gap-2 mt-2 text-sm text-slate-300">
                            <div className="grid grid-cols-[100px_1fr] gap-2">
                              <span className="text-slate-500">Source URL:</span>
                              <a href={task.url} target="_blank" rel="noreferrer" className="text-blue-400 hover:underline truncate">{task.url}</a>
                            </div>
                            <div className="grid grid-cols-[100px_1fr] gap-2">
                              <span className="text-slate-500">Format ID:</span>
                              <span className="font-mono bg-white/5 px-2 py-0.5 rounded text-xs w-fit">{task.format_id || "best (Auto)"}</span>
                            </div>
                            {task.local_url && (
                              <div className="grid grid-cols-[100px_1fr] gap-2">
                                <span className="text-slate-500">Saved to:</span>
                                <span className="text-slate-300 truncate font-mono text-xs">{task.local_url}</span>
                              </div>
                            )}
                          </div>
                        </AccordionContent>
                      </AccordionItem>
                    ))}
                  </Accordion>
                )}
              </div>
            </CardContent>
          </Card>
        </main>
      </div>
    </div>
  );
}
