import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './client';
import type {
    SendStakeholderEmailRequest,
    SentEmail,
    SentEmailDetail,
} from '@/types/email';

interface OAuthUrlResponse {
    authUrl: string;
    state: string;
}

interface SendStakeholderEmailResponse {
    success: boolean;
    message: string;
    messageId?: string;
}

interface SentEmailListResponse {
    emails: SentEmail[];
    total: number;
}

export const useEmailAuth = () => {
    return useMutation({
        mutationFn: async (userId: string) => {
            const response = await apiClient.get<OAuthUrlResponse>(
                '/email/authorize',
                { params: { user_id: userId } }
            );
            return response.data;
        },
    });
};

export const useSendStakeholderEmail = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (data: SendStakeholderEmailRequest & { user_id: string }) => {
            const response = await apiClient.post<SendStakeholderEmailResponse>(
                '/email/send/stakeholder',
                data
            );
            return response.data;
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({
                queryKey: ['stakeholder-emails', variables.case_id, variables.stakeholder_id],
            });
            queryClient.invalidateQueries({
                queryKey: ['cases', variables.case_id],
            });
        },
    });
};

export const useGenerateStakeholderPDF = () => {
    return useMutation({
        mutationFn: async (data: {
            stakeholder_id: string;
            case_id: string;
            content_type: 'full_documents' | 'pages_only' | 'chunks_only';
        }) => {
            const response = await apiClient.post(
                `/pdf/stakeholders/${data.stakeholder_id}/generate`,
                {
                    case_id: data.case_id,
                    content_type: data.content_type,
                },
                {
                    responseType: 'blob',
                }
            );

            const blob = new Blob([response.data], { type: 'application/pdf' });
            const url = window.URL.createObjectURL(blob);

            return {
                success: true,
                message: 'PDF generated successfully',
                blob,
                url,
                filename: `stakeholder-${data.stakeholder_id}-${Date.now()}.pdf`,
            };
        },
    });
};

export const useStakeholderEmails = (
    stakeholderId: string | undefined,
    caseId: string | undefined,
    stakeholderContactInfo?: string
) => {
    return useQuery({
        queryKey: ['stakeholder-emails', caseId, stakeholderId],
        queryFn: async () => {
            if (!stakeholderId || !caseId) return [];

            const response = await apiClient.get<SentEmailListResponse>(
                '/email/sent',
                {
                    params: { case_id: caseId },
                }
            );

            // Filter emails by stakeholder recipient if contact_info is provided
            let emails = response.data.emails;
            if (stakeholderContactInfo) {
                emails = emails.filter((email) =>
                    email.toRecipients.some(
                        (recipient) => recipient.address.toLowerCase() === stakeholderContactInfo.toLowerCase()
                    )
                );
            }

            return emails;
        },
        enabled: !!stakeholderId && !!caseId,
    });
};

export const useEmailReplies = (emailId: string | undefined) => {
    return useQuery({
        queryKey: ['email-replies', emailId],
        queryFn: async () => {
            if (!emailId) return [];

            const response = await apiClient.get<SentEmailDetail>(
                `/email/sent/${emailId}`
            );
            return response.data.replies || [];
        },
        enabled: !!emailId,
    });
};

export const useSyncEmailReplies = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (emailId: string) => {
            const response = await apiClient.post(`/email/sent/${emailId}/sync-replies`);
            return response.data;
        },
        onSuccess: (_, emailId) => {
            queryClient.invalidateQueries({
                queryKey: ['email-replies', emailId],
            });
            queryClient.invalidateQueries({
                queryKey: ['stakeholder-emails'],
            });
        },
    });
};

