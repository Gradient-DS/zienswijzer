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
            return {
                ...document,
                chunks: document.chunks?.map(transformChunkDetail) || [],
            } as Document;
        },
        enabled: !!documentId,
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

