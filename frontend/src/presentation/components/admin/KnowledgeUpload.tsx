import { useState, useRef } from 'react';
import { Upload, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { apiClient } from '../../../infrastructure/api/apiClient';

interface KnowledgeUploadProps {
    onUploadComplete: () => void;
}

export function KnowledgeUpload({ onUploadComplete }: KnowledgeUploadProps) {
    const [isUploading, setIsUploading] = useState(false);
    const [status, setStatus] = useState<"idle" | "success" | "error">("idle");
    const [errorMsg, setErrorMsg] = useState("");
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setIsUploading(true);
        setStatus("idle");
        setErrorMsg("");

        try {
            await apiClient.uploadKnowledge(file);
            setStatus("success");
            onUploadComplete();
            // Reset input
            if (fileInputRef.current) fileInputRef.current.value = "";
        } catch (err: any) {
            console.error(err);
            setStatus("error");
            setErrorMsg(err.response?.data?.detail || "Upload failed");
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="p-6 border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-center group">
            <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                accept=".txt,.md,.pdf" // Simplified for MVP
                onChange={handleFileChange}
                id="knowledge-upload"
            />
            <label htmlFor="knowledge-upload" className="cursor-pointer flex flex-col items-center justify-center gap-3">
                <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform">
                    {isUploading ? (
                        <Loader2 className="w-6 h-6 animate-spin" />
                    ) : (
                        <Upload className="w-6 h-6" />
                    )}
                </div>
                <div>
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                        {isUploading ? "Uploading & Processing..." : "Click to upload document"}
                    </h3>
                    <p className="text-xs text-gray-500 mt-1 max-w-xs mx-auto">
                        Supports .txt and .md files. Automatically chunked and embedded into Vector Store.
                    </p>
                </div>
            </label>

            {status === "success" && (
                <div className="mt-4 flex items-center justify-center gap-2 text-green-600 text-sm font-medium animate-in fade-in slide-in-from-bottom-2">
                    <CheckCircle className="w-4 h-4" />
                    Upload successful!
                </div>
            )}

            {status === "error" && (
                <div className="mt-4 flex items-center justify-center gap-2 text-red-600 text-sm font-medium animate-in fade-in slide-in-from-bottom-2">
                    <AlertCircle className="w-4 h-4" />
                    {errorMsg}
                </div>
            )}
        </div>
    );
}
