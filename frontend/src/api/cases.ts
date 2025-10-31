import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './client';
import { transformChunkDetail } from '@/lib/mention-utils';
import type { Case, CaseDetail, ChunkDetail } from '@/types';

interface CaseListResponse {
    cases: Case[];
}

interface CaseDetailResponse {
    case: CaseDetail;
}

interface CreateCaseRequest {
    title: string;
    description: string;
    password?: string;
}

interface CreateCaseResponse {
    case: Case;
}

export const useCases = () => {
    return useQuery({
        queryKey: ['cases'],
        queryFn: async () => {
            const res = await apiClient.get<CaseListResponse>('/cases');
            return res.data.cases;
        },
    });
};

export const useCase = (caseId: string | undefined) => {
    return useQuery({
        queryKey: ['cases', caseId],
        queryFn: async () => {
            const res = await apiClient.get<CaseDetailResponse>(`/cases/${caseId}`);
            return res.data.case;
        },
        enabled: !!caseId,
    });
};

interface UpdateCaseRequest {
    id: string;
    title: string;
    description: string;
}

interface UpdateCaseResponse {
    case: Case;
}

export const useCreateCase = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (data: CreateCaseRequest) =>
            apiClient.post<CreateCaseResponse>('/cases', data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['cases'] });
        },
    });
};

export const useUpdateCase = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (data: UpdateCaseRequest) =>
            apiClient.put<UpdateCaseResponse>(`/cases/${data.id}`, {
                title: data.title,
                description: data.description,
            }),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['cases'] });
            queryClient.invalidateQueries({ queryKey: ['cases', variables.id] });
        },
    });
};

export const useDocumentCompletionStatus = (caseId: string | undefined) => {
    return useQuery({
        queryKey: ['cases', caseId, 'document-completion'],
        queryFn: async () => {
            if (!caseId) return new Map<string, boolean>();

            try {
                const caseRes = await apiClient.get(`/cases/${caseId}`);
                const documents = caseRes.data.case.documents || [];

                const completionMap = new Map<string, boolean>();

                for (const doc of documents) {
                    try {
                        const chunksRes = await apiClient.get<any>(`/documents/${doc.id}/chunks`, {
                            params: { case_id: caseId }
                        });
                        const chunks = (chunksRes.data.chunks || []).map(transformChunkDetail) as ChunkDetail[];
                        const allMentions = chunks.flatMap((chunk: ChunkDetail) => chunk.stakeholder_mentions || []);

                        if (allMentions.length === 0) {
                            completionMap.set(doc.id, false);
                        } else {
                            const allChecked = allMentions.every((mention) => mention.checked);
                            completionMap.set(doc.id, allChecked);
                        }
                    } catch (error) {
                        console.error(`Failed to fetch chunks for document ${doc.id}:`, error);
                        completionMap.set(doc.id, false);
                    }
                }

                return completionMap;
            } catch (error) {
                console.error('Failed to fetch document completion status:', error);
                return new Map<string, boolean>();
            }
        },
        enabled: !!caseId,
        staleTime: 30000, // Cache for 30 seconds
    });
};

export interface ObjectedChunk {
    chunk_id: string;
    document_id: string;
    document_title: string;
    page: number;
    context: string;
    stakeholder_id: string;
    stakeholder_name: string;
}

export interface DocumentStatus {
    document_id: string;
    document_title: string;
    is_ok: boolean;
    objected_chunks: ObjectedChunk[];
}

export interface StakeholderResponse {
    stakeholder_id: string;
    stakeholder_name: string;
    publication_status: string | null;
    has_replied: boolean;
}

export interface CaseOverview {
    case_id: string;
    case_title: string;
    documents: DocumentStatus[];
    stakeholders: StakeholderResponse[];
    total_documents: number;
    total_objected_chunks: number;
    all_stakeholders_responded: boolean;
}

export const useCaseOverview = (caseId: string | undefined) => {
    return useQuery({
        queryKey: ['cases', caseId, 'overview'],
        queryFn: async () => {
            if (!caseId) return null;
            const res = await apiClient.get<CaseOverview>(`/cases/${caseId}/overview`);
            return res.data;
        },
        enabled: !!caseId,
    });
};

