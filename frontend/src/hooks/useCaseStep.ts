import { useSearchParams, useNavigate, useLocation } from 'react-router-dom';

export type CaseStep = 'create' | 'review' | 'belanghebbenden';

const STEP_NAMES: Record<CaseStep, string> = {
    create: 'Zaak aanmaken',
    review: 'documenten controleren',
    belanghebbenden: 'belanghebbenden',
};

export function useCaseStep() {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const location = useLocation();

    const pathStep = searchParams.get('step') as CaseStep | null;
    const isNewCase = location.pathname === '/cases/new';
    const hasCaseId = location.pathname.match(/\/cases\/(.+)/) !== null;

    const step: CaseStep = pathStep || (isNewCase ? 'create' : hasCaseId ? 'review' : 'create');

    const setStep = (newStep: CaseStep, caseId?: string) => {
        const path = caseId ? `/cases/${caseId}` : '/cases/new';
        navigate(`${path}?step=${newStep}`);
    };

    const getStepName = (stepKey: CaseStep) => STEP_NAMES[stepKey];

    return {
        step,
        setStep,
        getStepName,
        STEP_NAMES,
    };
}

