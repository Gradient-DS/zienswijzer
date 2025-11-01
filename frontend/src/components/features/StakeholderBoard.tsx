import { useCaseStakeholders, useAllStakeholderMentions } from '@/api/stakeholders';
import { useAllCaseEmails } from '@/api/email';
import type { StakeholderStatus } from '@/lib/stakeholder-status';
import type { Stakeholder, ChunkDetail } from '@/types';
import type { SentEmail } from '@/types/email';
import { FileText, Clock, Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import { StakeholderBoardItem } from './StakeholderBoardItem';

interface StakeholderBoardProps {
    caseId: string;
    onSelectStakeholder: (stakeholderId: string) => void;
}

interface StatusColumn {
    id: StakeholderStatus;
    title: string;
    subtitle?: string;
    icon: React.ReactNode;
    color: string;
}

export const STATUS_COLUMNS: StatusColumn[] = [
    {
        id: 'not_processed',
        title: 'Niet verwerkt',
        icon: <FileText className="h-4 w-4" />,
        color: 'text-gray-500',
    },
    {
        id: 'not_contacted',
        title: 'Niet gecontacteerd',
        icon: <Clock className="h-4 w-4" />,
        color: 'text-gray-500',
    },
    {
        id: 'contacted',
        title: 'Gecontacteerd',
        icon: <Clock className="h-4 w-4" />,
        color: 'text-green-600',
    },
    {
        id: 'contacted_old',
        title: 'Gecontacteerd',
        subtitle: '(> 1 uur)',
        icon: <Clock className="h-4 w-4" />,
        color: 'text-orange-600',
    },
    {
        id: 'responded',
        title: 'Gereageerd',
        icon: <Check className="h-5 w-5" />,
        color: 'text-green-600',
    },
];

export function StakeholderBoard({ caseId, onSelectStakeholder }: StakeholderBoardProps) {
    const { data: stakeholders = [] } = useCaseStakeholders(caseId);
    const { data: allMentionsMap = new Map() } = useAllStakeholderMentions(caseId);
    const { data: allEmails = [] } = useAllCaseEmails(caseId);

    console.log('[StakeholderBoard] Total emails:', allEmails.length);
    console.log('[StakeholderBoard] All emails:', allEmails.map(e => ({
        id: e.id,
        stakeholderId: e.stakeholderId,
        to: e.toRecipients.map(r => r.address)
    })));

    return (
        <div className="h-full overflow-auto p-6">
            <div className="flex gap-2 h-full">
                {STATUS_COLUMNS.map(column => (
                    <StakeholderBoardColumn
                        key={column.id}
                        column={column}
                        stakeholders={stakeholders}
                        onSelectStakeholder={onSelectStakeholder}
                        allMentionsMap={allMentionsMap}
                        allEmails={allEmails}
                    />
                ))}
            </div>
        </div>
    );
}

function StakeholderBoardColumn({
    column,
    stakeholders,
    onSelectStakeholder,
    allMentionsMap,
    allEmails,
}: {
    column: StatusColumn;
    stakeholders: Stakeholder[];
    onSelectStakeholder: (stakeholderId: string) => void;
    allMentionsMap: Map<string, ChunkDetail[]>;
    allEmails: SentEmail[];
}) {
    // Filter stakeholders that belong in this column based on their status
    const stakeholdersInColumn = stakeholders.filter(stakeholder => {
        const chunks = allMentionsMap.get(stakeholder.id) || [];

        if (!chunks || chunks.length === 0) {
            return column.id === 'not_processed';
        }

        const filteredEmails = allEmails.filter(email => {
            if (email.stakeholderId && email.stakeholderId === stakeholder.id) {
                return true;
            }
            if (stakeholder.contact_info) {
                return email.toRecipients.some(
                    recipient => recipient.address.toLowerCase().trim() === stakeholder.contact_info.toLowerCase().trim()
                );
            }
            return false;
        });

        const allMentions = chunks.flatMap(chunk => chunk.stakeholder_mentions);
        const allProcessed = allMentions.length > 0 && allMentions.every(mention => mention.checked);

        if (!allProcessed) {
            return column.id === 'not_processed';
        }

        if (filteredEmails.length === 0) {
            return column.id === 'not_contacted';
        }

        const mostRecentEmail = filteredEmails.sort((a, b) =>
            new Date(b.sentAt).getTime() - new Date(a.sentAt).getTime()
        )[0];

        const emailTime = new Date(mostRecentEmail.sentAt).getTime();
        const now = Date.now();
        const hoursSinceEmail = (now - emailTime) / (1000 * 60 * 60);

        if (hoursSinceEmail > 1) {
            return column.id === 'contacted_old';
        }

        return column.id === 'contacted';
    });

    return (
        <div className="flex-1 flex flex-col min-w-0 bg-gray-50 rounded-lg border-2 border-gray-200">
            {/* Column Header */}
            <div className="flex items-start gap-2 p-4 min-h-[72px] border-b border-gray-200 bg-white rounded-t-lg">
                <div className={cn('flex-shrink-0 mt-0.5', column.color)}>
                    {column.icon}
                </div>
                <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-sm text-gray-900 leading-tight">
                        {column.title}
                    </h3>
                    {column.subtitle && (
                        <h3 className="font-semibold text-sm text-gray-900 leading-tight mt-0.5">
                            {column.subtitle}
                        </h3>
                    )}
                </div>
                <span className="px-2 py-0.5 rounded-full bg-gray-200 text-xs font-semibold text-gray-700 flex-shrink-0">
                    {stakeholdersInColumn.length}
                </span>
            </div>

            {/* Column Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-2">
                {stakeholders.length === 0 ? (
                    <div className="text-center py-8 text-gray-400 text-sm">
                        Geen belanghebbenden
                    </div>
                ) : stakeholdersInColumn.length === 0 ? (
                    <div className="text-center py-8 text-gray-400 text-sm">
                        Geen items
                    </div>
                ) : (
                    stakeholdersInColumn.map(stakeholder => {
                        const filteredEmails = allEmails.filter(email => {
                            if (email.stakeholderId && email.stakeholderId === stakeholder.id) {
                                return true;
                            }
                            if (stakeholder.contact_info) {
                                return email.toRecipients.some(
                                    recipient => recipient.address.toLowerCase().trim() === stakeholder.contact_info.toLowerCase().trim()
                                );
                            }
                            return false;
                        });

                        return (
                            <StakeholderBoardItem
                                key={stakeholder.id}
                                stakeholder={stakeholder}
                                targetStatus={column.id}
                                onClick={() => onSelectStakeholder(stakeholder.id)}
                                chunks={allMentionsMap.get(stakeholder.id) || []}
                                sentEmails={filteredEmails}
                            />
                        );
                    })
                )}
            </div>
        </div>
    );
}
