import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './client';
import type { Document } from '@/types';
import { transformChunkDetail } from '@/lib/mention-utils';

export const useDocument = (documentId: string | undefined, caseId?: string | undefined) => {
    return useQuery({
        queryKey: ['documents', documentId, caseId],
        queryFn: async () => {
            const res = await apiClient.get<any>(`/documents/${documentId}`, {
                params: caseId ? { case_id: caseId } : {}
            });
            const document = res.data.document || res.data;
            const processedDoc = {
                ...document,
                chunks: document.chunks?.map(transformChunkDetail) || [],
            } as Document;

            // Debug logging
            if (import.meta.env.DEV) {
                console.log('[useDocument] Fetched document:', {
                    id: documentId?.substring(0, 8),
                    parse_status: processedDoc.parse_status,
                    page_count: processedDoc.page_count,
                    chunks_count: processedDoc.chunks?.length || 0
                });
            }

            return processedDoc;
        },
        enabled: !!documentId,
        refetchInterval: (query) => {
            const data = query.state.data;

            // Stop polling if status is explicitly failed
            if (data?.parse_status === 'failed') {
                return false;
            }

            // Stop polling if we have chunks (meaning NER processing is done)
            // Regardless of parse_status (backend uses both "parsed" and "completed")
            const hasProcessedChunks = data?.chunks && data.chunks.length > 0;

            if (hasProcessedChunks) {
                return false; // Chunks are ready, stop polling
            }

            // Continue polling if:
            // - Document is pending/processing (no chunks yet)
            // - Document has page_count but no chunks yet (PDF parsed, NER not done)
            return 2000;
        },
    });
};

export const useUploadDocument = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ caseId, file }: { caseId: string; file: File }) => {
            const formData = new FormData();
            formData.append('file', file);

            const res = await apiClient.post(
                `/documents/upload?case_id=${caseId}`,
                formData,
                {
                    headers: {
                        // Delete Content-Type to let axios set it automatically with boundary for FormData
                    },
                    transformRequest: (data, headers) => {
                        delete headers['Content-Type'];
                        return data;
                    },
                }
            );
            return res.data;
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['cases', variables.caseId] });
            queryClient.invalidateQueries({ queryKey: ['documents'] });
        },
    });
};

export const useRemoveDocumentFromCase = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ caseId, documentId }: { caseId: string; documentId: string }) => {
            const res = await apiClient.delete(`/cases/${caseId}/documents/${documentId}`);
            return res.data;
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['cases', variables.caseId] });
            queryClient.invalidateQueries({ queryKey: ['documents'] });
        },
    });
};

export const getDocumentPdfUrl = (documentId: string): string => {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    return `${baseUrl}/documents/${documentId}/pdf`;
};

