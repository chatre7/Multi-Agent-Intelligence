import { useState } from 'react';
import { FileText, Trash2, Calendar, Database } from 'lucide-react';
import { apiClient } from '../../../infrastructure/api/apiClient';

interface KnowledgeDocument {
    id: string;
    filename: string;
    content_type: string;
    size_bytes: number;
    created_at: string;
    status: string;
}

interface KnowledgeListProps {
    documents: KnowledgeDocument[];
    onDelete: (id: string) => void;
    isLoading: boolean;
}

export function KnowledgeList({ documents, onDelete, isLoading }: KnowledgeListProps) {
    const [deletingId, setDeletingId] = useState<string | null>(null);

    const handleDelete = async (id: string) => {
        if (!confirm("Are you sure? This will delete the document and all associated embeddings.")) return;

        setDeletingId(id);
        try {
            await apiClient.deleteKnowledge(id);
            onDelete(id);
        } catch (error) {
            console.error("Failed to delete", error);
            alert("Failed to delete document");
        } finally {
            setDeletingId(null);
        }
    };

    if (isLoading) {
        return <div className="space-y-3">
            {[1, 2, 3].map(i => <div key={i} className="h-16 bg-gray-100 dark:bg-gray-800 animate-pulse rounded-lg" />)}
        </div>;
    }

    if (documents.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-12 text-gray-400 border border-dashed border-gray-200 dark:border-gray-800 rounded-lg">
                <Database className="w-10 h-10 mb-2 opacity-50" />
                <p>No knowledge documents found.</p>
            </div>
        );
    }

    return (
        <div className="space-y-3">
            {documents.map((doc) => (
                <div key={doc.id} className="flex items-center justify-between p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-center gap-4">
                        <div className="w-10 h-10 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 rounded-lg flex items-center justify-center">
                            <FileText className="w-5 h-5" />
                        </div>
                        <div>
                            <h4 className="font-medium text-gray-900 dark:text-white truncate max-w-[300px]" title={doc.filename}>
                                {doc.filename}
                            </h4>
                            <div className="flex items-center gap-3 text-xs text-gray-500 mt-1">
                                <span className="flex items-center gap-1">
                                    <Calendar className="w-3 h-3" />
                                    {new Date(doc.created_at).toLocaleDateString()}
                                </span>
                                <span className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-gray-600 dark:text-gray-300">
                                    {(doc.size_bytes / 1024).toFixed(1)} KB
                                </span>
                                <span className={`px-1.5 py-0.5 rounded capitalize ${doc.status === 'processed'
                                    ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                                    : 'bg-yellow-100 text-yellow-700'
                                    }`}>
                                    {doc.status}
                                </span>
                            </div>
                        </div>
                    </div>

                    <button
                        onClick={() => handleDelete(doc.id)}
                        disabled={deletingId === doc.id}
                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors disabled:opacity-50"
                        title="Delete Document"
                    >
                        {deletingId === doc.id ? (
                            <div className="w-4 h-4 border-2 border-red-600 border-t-transparent rounded-full animate-spin" />
                        ) : (
                            <Trash2 className="w-4 h-4" />
                        )}
                    </button>
                </div>
            ))}
        </div>
    );
}
