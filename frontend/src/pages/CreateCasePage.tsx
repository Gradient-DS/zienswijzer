import { useEffect, useState } from 'react';
import { BreadcrumbNavigation } from '@/components/features/BreadcrumbNavigation';
import { CreateCaseForm } from '@/components/features/CreateCaseForm';
import { useUIStore } from '@/store';
import { cn } from '@/lib/utils';

export default function CreateCasePage() {
    const { isSidebarOpen } = useUIStore();
    const [isMobile, setIsMobile] = useState(false);

    useEffect(() => {
        const checkMobile = () => {
            setIsMobile(window.innerWidth < 1024);
        };
        checkMobile();
        window.addEventListener('resize', checkMobile);
        return () => window.removeEventListener('resize', checkMobile);
    }, []);

    return (
        <div className="h-full flex flex-col">
            <div className={cn(
                "border-b bg-white",
                isMobile ? "px-4 pb-3 -mt-12" : "px-6 pt-4 pb-3",
                !isMobile && !isSidebarOpen && "pl-[72px]"
            )}>
                <BreadcrumbNavigation />
            </div>

            <div className="flex-1 bg-gray-100 overflow-hidden">
                <CreateCaseForm />
            </div>
        </div>
    );
}

