import { useState, useCallback } from "react";
import { apiClient } from "../../infrastructure/api/apiClient";

export interface KnowledgeDocument {
    id: string;
    filename: string;
    content_type: string;
    size_bytes: number;
    created_at: string;
    status: string;
}

export function useKnowledge() {
    const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchDocuments = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        try {
            const docs = await apiClient.listKnowledge();
            setDocuments(docs);
        } catch (err: any) {
            console.error("Failed to fetch documents", err);
            setError(err.message || "Failed to load documents");
        } finally {
            setIsLoading(false);
        }
    }, []);

    const uploadDocument = useCallback(async (file: File) => {
        setIsLoading(true);
        setError(null);
        try {
            await apiClient.uploadKnowledge(file);
            await fetchDocuments(); // Refresh list after upload
        } catch (err: any) {
            console.error("Failed to upload document", err);
            setError(err.message || "Failed to upload document");
            throw err; // Re-throw to let component handle specific UI feedback
        } finally {
            setIsLoading(false);
        }
    }, [fetchDocuments]);

    const deleteDocument = useCallback(async (id: string) => {
        // Optimistic update could go here, but for simplicity we wait
        try {
            await apiClient.deleteKnowledge(id);
            setDocuments(prev => prev.filter(doc => doc.id !== id));
        } catch (err: any) {
            console.error("Failed to delete document", err);
            setError(err.message || "Failed to delete document");
            throw err;
        }
    }, []);

    return {
        documents,
        isLoading,
        error,
        fetchDocuments,
        uploadDocument,
        deleteDocument
    };
}
