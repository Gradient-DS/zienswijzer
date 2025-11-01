import { useState, useEffect, useRef } from 'react';
import { useCaseStakeholders } from '@/api/stakeholders';
import type { StakeholderStatus } from '@/lib/stakeholder-status';
import type { Stakeholder } from '@/types';
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

    return (
        <div className="h-full overflow-auto p-6">
            <div className="flex gap-2 h-full">
                {STATUS_COLUMNS.map(column => (
                    <StakeholderBoardColumn
                        key={column.id}
                        column={column}
                        stakeholders={stakeholders}
                        caseId={caseId}
                        onSelectStakeholder={onSelectStakeholder}
                    />
                ))}
            </div>
        </div>
    );
}

function StakeholderBoardColumn({
    column,
    stakeholders,
    caseId,
    onSelectStakeholder,
}: {
    column: StatusColumn;
    stakeholders: Stakeholder[];
    caseId: string;
    onSelectStakeholder: (stakeholderId: string) => void;
}) {
    const [visibleCount, setVisibleCount] = useState(0);
    const renderedItemsRef = useRef(new Set<string>());

    useEffect(() => {
        // Reset count when stakeholders change
        renderedItemsRef.current.clear();
        setVisibleCount(0);
    }, [stakeholders, column.id]);

    const handleItemRender = (stakeholderId: string, rendered: boolean) => {
        if (rendered) {
            renderedItemsRef.current.add(stakeholderId);
        } else {
            renderedItemsRef.current.delete(stakeholderId);
        }
        setVisibleCount(renderedItemsRef.current.size);
    };

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
                    {visibleCount}
                </span>
            </div>

            {/* Column Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-2">
                {stakeholders.length === 0 ? (
                    <div className="text-center py-8 text-gray-400 text-sm">
                        Geen belanghebbenden
                    </div>
                ) : (
                    stakeholders.map(stakeholder => (
                        <StakeholderBoardItem
                            key={stakeholder.id}
                            stakeholder={stakeholder}
                            targetStatus={column.id}
                            caseId={caseId}
                            onClick={() => onSelectStakeholder(stakeholder.id)}
                            onRender={(id, rendered) => handleItemRender(id, rendered)}
                        />
                    ))
                )}
            </div>
        </div>
    );
}
