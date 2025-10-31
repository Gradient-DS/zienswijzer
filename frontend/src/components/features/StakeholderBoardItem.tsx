import { useMemo, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { useStakeholderMentions } from '@/api/stakeholders';
import { useStakeholderEmails } from '@/api/email';
import { getStakeholderStatus } from '@/lib/stakeholder-status';
import type { StakeholderStatus } from '@/lib/stakeholder-status';
import type { Stakeholder } from '@/types';
import { Users } from 'lucide-react';
import { cn } from '@/lib/utils';
import { STATUS_COLUMNS } from './StakeholderBoard';

interface StakeholderBoardItemProps {
    stakeholder: Stakeholder;
    targetStatus: StakeholderStatus;
    caseId: string;
    onClick: () => void;
    onRender?: (stakeholderId: string, rendered: boolean) => void;
}

export function StakeholderBoardItem({
    stakeholder,
    targetStatus,
    caseId,
    onClick,
    onRender,
}: StakeholderBoardItemProps) {
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

    // Only render if this stakeholder's status matches the column
    if (status !== targetStatus) {
        onRender?.(stakeholder.id, false);
        return null;
    }

    // Call onRender in useEffect to ensure it's called after render
    useEffect(() => {
        onRender?.(stakeholder.id, true);
        return () => {
            onRender?.(stakeholder.id, false);
        };
    }, [stakeholder.id, onRender]);

    const statusColumn = STATUS_COLUMNS.find(col => col.id === status);

    return (
        <Card
            className={cn(
                'mb-3 cursor-pointer hover:shadow-md transition-all border-2',
                'hover:border-primary'
            )}
            onClick={onClick}
        >
            <CardContent className="p-4">
                <div className="flex items-start gap-3">
                    <Users className={cn('h-4 w-4 flex-shrink-0 mt-0.5', statusColumn?.color)} />
                    <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-sm text-gray-900 truncate">
                            {stakeholder.name}
                        </h3>
                        <div className="flex items-center gap-2 mt-1">
                            <span className="text-xs text-gray-500 capitalize">
                                {stakeholder.type}
                            </span>
                            {stakeholder.contact_info && (
                                <>
                                    <span className="text-xs text-gray-400">•</span>
                                    <span className="text-xs text-gray-500 truncate">
                                        {stakeholder.contact_info}
                                    </span>
                                </>
                            )}
                        </div>
                    </div>
                    {statusColumn && (
                        <div className={cn('flex-shrink-0', statusColumn.color)}>
                            {statusColumn.icon}
                        </div>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}

