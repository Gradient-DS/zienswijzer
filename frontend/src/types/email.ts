export interface EmailAddress {
    address: string;
    name?: string;
}

export type ContentType = 'full_documents' | 'pages_only' | 'chunks_only';

export interface SendStakeholderEmailRequest {
    stakeholder_id: string;
    case_id: string;
    content_type: ContentType;
    to: EmailAddress[];
    subject: string;
    custom_message?: string;
    cc?: EmailAddress[];
    bcc?: EmailAddress[];
}

export interface SentEmail {
    id: string;
    userId: string;
    subject: string;
    body: string;
    bodyType: string;
    toRecipients: EmailAddress[];
    ccRecipients?: EmailAddress[];
    bccRecipients?: EmailAddress[];
    importance: string;
    outlookMessageId?: string;
    outlookConversationId?: string;
    trackingId?: string;
    sentAt: string;
    caseId?: string;
    stakeholderId?: string;
    createdAt: string;
}

export interface EmailReply {
    id: string;
    sentEmailId: string;
    outlookMessageId: string;
    fromAddress: EmailAddress;
    subject: string;
    bodyPreview: string;
    body?: string;
    bodyType: string;
    receivedAt: string;
    isRead: boolean;
    hasAttachments: boolean;
    importance: string;
    createdAt: string;
    updatedAt: string;
}

export interface SentEmailDetail extends SentEmail {
    replies: EmailReply[];
}

export interface EmailTimelineItem {
    email: SentEmail;
    replies: EmailReply[];
    syncStatus: 'synced' | 'pending' | 'error';
}

