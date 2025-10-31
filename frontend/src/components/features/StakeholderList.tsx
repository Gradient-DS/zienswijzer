import type { Stakeholder } from '@/types';
import { Users, CheckCircle2, FileText, Clock } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useStakeholderMentions } from '@/api/stakeholders';
import { useStakeholderEmails } from '@/api/email';
import { useMemo } from 'react';
import { getStakeholderStatus } from '@/lib/stakeholder-status';
import type { StakeholderStatus } from '@/lib/stakeholder-status';

interface StakeholderListProps {
    stakeholders: Stakeholder[];
    selectedStakeholderId?: string;
    onSelectStakeholder?: (stakeholderId: string) => void;
    verifiedStakeholderIds?: Set<string>;
    caseId?: string;
}

function StatusIcon({ status }: { status: StakeholderStatus }) {
    switch (status) {
        case 'not_processed':
            return <FileText className="h-4 w-4 text-gray-500 flex-shrink-0 mt-0.5" />;
        case 'not_contacted':
            return <Clock className="h-4 w-4 text-gray-500 flex-shrink-0 mt-0.5" />;
        case 'contacted':
            return <Clock className="h-4 w-4 text-green-600 flex-shrink-0 mt-0.5" />;
        case 'contacted_old':
            return <Clock className="h-4 w-4 text-orange-600 flex-shrink-0 mt-0.5" />;
        case 'responded':
            return <CheckCircle2 className="h-4 w-4 text-green-600 flex-shrink-0 mt-0.5" />;
        default:
            return <FileText className="h-4 w-4 text-gray-500 flex-shrink-0 mt-0.5" />;
    }
}

export function StakeholderList({
    stakeholders,
    selectedStakeholderId,
    onSelectStakeholder,
    caseId,
}: StakeholderListProps) {
    if (stakeholders.length === 0) {
        return (
            <div className="text-center py-8 text-muted-foreground">
                <p>Geen belanghebbenden beschikbaar</p>
            </div>
        );
    }

    const uniqueStakeholders = Array.from(
        new Map(stakeholders.map(s => [s.id, s])).values()
    );

    return (
        <div className="space-y-1">
            {uniqueStakeholders.map((stakeholder) => (
                <StakeholderListItem
                    key={stakeholder.id}
                    stakeholder={stakeholder}
                    selectedStakeholderId={selectedStakeholderId}
                    onSelectStakeholder={onSelectStakeholder}
                    caseId={caseId}
                />
            ))}
        </div>
    );
}

function StakeholderListItem({
    stakeholder,
    selectedStakeholderId,
    onSelectStakeholder,
    caseId,
}: {
    stakeholder: Stakeholder;
    selectedStakeholderId?: string;
    onSelectStakeholder?: (stakeholderId: string) => void;
    caseId?: string;
}) {
    const { data: chunks } = useStakeholderMentions(caseId, stakeholder.id);
    const { data: sentEmails = [] } = useStakeholderEmails(
        stakeholder.id,
        caseId,
        stakeholder.contact_info
    );

    const status = useMemo(() => {
        if (!chunks || chunks.length === 0) {
            return 'not_processed' as StakeholderStatus;
        }
        return getStakeholderStatus({
            chunks,
            sentEmails,
            stakeholderId: stakeholder.id,
            contactInfo: stakeholder.contact_info,
        });
    }, [chunks, sentEmails, stakeholder.id, stakeholder.contact_info]);

    return (
        <div
            className={cn(
                'flex items-start gap-2 px-2 py-2 rounded-md cursor-pointer transition-colors relative',
                selectedStakeholderId === stakeholder.id
                    ? 'bg-gray-200 text-gray-900'
                    : 'hover:bg-gray-100 text-gray-700'
            )}
            onClick={() => onSelectStakeholder?.(stakeholder.id)}
        >
            <Users className="h-4 w-4 text-muted-foreground flex-shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate">
                    {stakeholder.name}
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-xs text-muted-foreground">
                        {stakeholder.type}
                    </span>
                    {stakeholder.contact_info && (
                        <span className="text-xs text-muted-foreground truncate">
                            {stakeholder.contact_info}
                        </span>
                    )}
                </div>
            </div>
            <StatusIcon status={status} />
        </div>
    );
}

