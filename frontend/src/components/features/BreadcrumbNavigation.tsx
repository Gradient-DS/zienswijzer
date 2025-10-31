import { ChevronRight } from 'lucide-react';
import { useCaseStep, type CaseStep } from '@/hooks/useCaseStep';
import { cn } from '@/lib/utils';

interface BreadcrumbNavigationProps {
    caseId?: string;
}

export function BreadcrumbNavigation({ caseId }: BreadcrumbNavigationProps) {
    const { step, setStep, STEP_NAMES } = useCaseStep();

    const steps: CaseStep[] = ['create', 'review', 'contact'];

    const handleStepClick = (stepKey: CaseStep) => {
        if (stepKey === 'review' && !caseId) {
            return;
        }
        if (stepKey === 'contact' && !caseId) {
            return;
        }
        setStep(stepKey, caseId);
    };

    const isStepEnabled = (stepKey: CaseStep): boolean => {
        if (stepKey === 'create') return true;
        if (stepKey === 'review' || stepKey === 'contact') return !!caseId;
        return false;
    };

    const getStepLabel = (stepKey: CaseStep): string => {
        if (stepKey === 'create' && caseId) {
            return 'Zaak bewerken';
        }
        return STEP_NAMES[stepKey];
    };

    return (
        <nav aria-label="Breadcrumb" className="flex items-center gap-2 flex-wrap">
            {steps.map((stepKey, index) => {
                const isActive = step === stepKey;
                const isEnabled = isStepEnabled(stepKey);
                const isLast = index === steps.length - 1;

                return (
                    <div key={stepKey} className="flex items-center gap-2">
                        <button
                            type="button"
                            onClick={() => handleStepClick(stepKey)}
                            disabled={!isEnabled || isActive}
                            className={cn(
                                'text-sm font-medium transition-colors',
                                isActive
                                    ? 'text-primary'
                                    : isEnabled
                                        ? 'text-muted-foreground hover:text-foreground cursor-pointer'
                                        : 'text-muted-foreground/50 cursor-not-allowed'
                            )}
                        >
                            {getStepLabel(stepKey)}
                        </button>
                        {!isLast && (
                            <ChevronRight
                                className={cn(
                                    'h-4 w-4',
                                    isEnabled ? 'text-muted-foreground' : 'text-muted-foreground/50'
                                )}
                            />
                        )}
                    </div>
                );
            })}
        </nav>
    );
}

