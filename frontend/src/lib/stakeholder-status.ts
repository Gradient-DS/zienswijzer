import type { ChunkDetail, SentEmail, EmailReply } from '@/types';

export type StakeholderStatus =
    | 'not_processed'      // Gray document icon - chunks not yet fully processed
    | 'not_contacted'       // Gray clock icon - processed but not contacted
    | 'contacted'           // Green clock icon - contacted recently (< 1 hour)
    | 'contacted_old'       // Orange clock icon - contacted more than 1 hour ago
    | 'responded';          // Green check mark - has replied

interface StakeholderStatusParams {
    chunks: ChunkDetail[];
    sentEmails: SentEmail[];
    stakeholderId: string;
    contactInfo?: string; // Optional contact info for matching emails
}

export function getStakeholderStatus({
    chunks,
    sentEmails,
    stakeholderId,
    contactInfo,
}: StakeholderStatusParams): StakeholderStatus {
    // Check if all chunks are processed (checked)
    const allMentions = chunks.flatMap(chunk => chunk.stakeholder_mentions);
    const allProcessed = allMentions.length > 0 && allMentions.every(mention => mention.checked);

    if (!allProcessed) {
        return 'not_processed';
    }

    // Filter emails for this stakeholder
    // Note: sentEmails should already be filtered by useStakeholderEmails, but we check both
    // stakeholderId (if available) and contactInfo as fallback
    const stakeholderEmails = sentEmails.filter(email => {
        // If email has stakeholderId, match by that
        if (email.stakeholderId && email.stakeholderId === stakeholderId) {
            return true;
        }
        // Otherwise, match by contact info if available
        if (contactInfo) {
            return email.toRecipients.some(
                recipient => recipient.address.toLowerCase() === contactInfo.toLowerCase()
            );
        }
        // If no contact info, assume all emails in the filtered list are for this stakeholder
        // (since useStakeholderEmails already filtered by contact_info)
        return true;
    });

    if (stakeholderEmails.length === 0) {
        return 'not_contacted';
    }

    // Get the most recent email
    const mostRecentEmail = stakeholderEmails.sort((a, b) =>
        new Date(b.sentAt).getTime() - new Date(a.sentAt).getTime()
    )[0];

    // Check if there are any replies to any of the stakeholder emails
    // Note: This requires checking email replies, which we'll need to fetch
    // For now, we'll assume replies are passed in or we check via a different mechanism

    // Calculate time since most recent email
    const emailTime = new Date(mostRecentEmail.sentAt).getTime();
    const now = Date.now();
    const hoursSinceEmail = (now - emailTime) / (1000 * 60 * 60);

    // If more than 1 hour ago, show orange clock
    if (hoursSinceEmail > 1) {
        return 'contacted_old';
    }

    // Otherwise, show green clock (contacted recently)
    return 'contacted';
}

export function getStakeholderStatusWithReplies({
    chunks,
    sentEmails,
    stakeholderId,
    contactInfo,
    emailRepliesMap, // Map of emailId -> EmailReply[]
}: StakeholderStatusParams & {
    emailRepliesMap?: Map<string, EmailReply[]>;
}): StakeholderStatus {
    // Check if all chunks are processed (checked)
    const allMentions = chunks.flatMap(chunk => chunk.stakeholder_mentions);
    const allProcessed = allMentions.length > 0 && allMentions.every(mention => mention.checked);

    if (!allProcessed) {
        return 'not_processed';
    }

    // Filter emails for this stakeholder (same logic as getStakeholderStatus)
    const stakeholderEmails = sentEmails.filter(email => {
        if (email.stakeholderId && email.stakeholderId === stakeholderId) {
            return true;
        }
        if (contactInfo) {
            return email.toRecipients.some(
                recipient => recipient.address.toLowerCase() === contactInfo.toLowerCase()
            );
        }
        return true;
    });

    if (stakeholderEmails.length === 0) {
        return 'not_contacted';
    }

    // Check if any email has replies
    if (emailRepliesMap) {
        const hasReplies = stakeholderEmails.some(email => {
            const replies = emailRepliesMap.get(email.id) || [];
            return replies.length > 0;
        });

        if (hasReplies) {
            return 'responded';
        }
    }

    // Get the most recent email
    const mostRecentEmail = stakeholderEmails.sort((a, b) =>
        new Date(b.sentAt).getTime() - new Date(a.sentAt).getTime()
    )[0];

    // Calculate time since most recent email
    const emailTime = new Date(mostRecentEmail.sentAt).getTime();
    const now = Date.now();
    const hoursSinceEmail = (now - emailTime) / (1000 * 60 * 60);

    // If more than 1 hour ago, show orange clock
    if (hoursSinceEmail > 1) {
        return 'contacted_old';
    }

    // Otherwise, show green clock (contacted recently)
    return 'contacted';
}

export function checkStakeholderHasReplies(_sentEmails: SentEmail[], _stakeholderId: string): boolean {
    // This is a placeholder - in practice, you'd need to check replies for each email
    // For now, we'll assume no replies unless explicitly checked via emailRepliesMap
    return false;
}

