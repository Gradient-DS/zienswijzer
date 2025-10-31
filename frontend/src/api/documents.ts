import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './client';
import type { Document } from '@/types';

interface DocumentDetailResponse {
    document: Document & {
        chunks?: unknown[];
    };
}

interface UploadDocumentResponse {
    document: Document;
}

export const useDocument = (documentId: string | undefined) => {
    return useQuery({
        queryKey: ['documents', documentId],
        queryFn: async () => {
            const res = await apiClient.get<DocumentDetailResponse>(`/documents/${documentId}`);
            return res.data.document;
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

            const res = await apiClient.post<UploadDocumentResponse>(
                `/documents/upload?case_id=${caseId}`,
                formData
            );
            return res.data.document;
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

