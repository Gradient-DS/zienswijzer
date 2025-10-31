import { useEffect, useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { AlertCircle, ExternalLink } from 'lucide-react';

interface EmailAuthDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    authUrl: string | null;
    onRetry?: () => void;
}

export function EmailAuthDialog({
    open,
    onOpenChange,
    authUrl,
    onRetry,
}: EmailAuthDialogProps) {
    const [authWindow, setAuthWindow] = useState<Window | null>(null);

    useEffect(() => {
        if (open && authUrl) {
            // Open OAuth window automatically
            const windowFeatures = 'width=600,height=700,scrollbars=yes,resizable=yes,left=100,top=100';
            const newWindow = window.open(authUrl, 'Microsoft OAuth', windowFeatures);
            setAuthWindow(newWindow);

            if (!newWindow) {
                // Popup blocked, show manual button
                return;
            }

            // Check if window is closed (user completed or cancelled OAuth)
            const checkClosed = setInterval(() => {
                if (newWindow.closed) {
                    clearInterval(checkClosed);
                    setAuthWindow(null);
                    // Close dialog after a short delay
                    setTimeout(() => {
                        onOpenChange(false);
                        if (onRetry) {
                            // Small delay before retry to allow backend to process callback
                            setTimeout(() => {
                                onRetry();
                            }, 1000);
                        }
                    }, 500);
                }
            }, 500);

            return () => {
                clearInterval(checkClosed);
            };
        }
    }, [open, authUrl, onOpenChange, onRetry]);

    const handleOpenWindow = () => {
        if (authUrl) {
            const windowFeatures = 'width=600,height=700,scrollbars=yes,resizable=yes,left=100,top=100';
            const newWindow = window.open(authUrl, 'Microsoft OAuth', windowFeatures);
            setAuthWindow(newWindow);

            if (newWindow) {
                // Monitor window close
                const checkClosed = setInterval(() => {
                    if (newWindow.closed) {
                        clearInterval(checkClosed);
                        setAuthWindow(null);
                        setTimeout(() => {
                            onOpenChange(false);
                            if (onRetry) {
                                setTimeout(() => {
                                    onRetry();
                                }, 1000);
                            }
                        }, 500);
                    }
                }, 500);
            }
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <AlertCircle className="h-5 w-5 text-yellow-600" />
                        E-mail autorisatie vereist
                    </DialogTitle>
                    <DialogDescription>
                        Om e-mails te kunnen versturen moet je eerst toegang geven tot je Microsoft Outlook account.
                    </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                    <p className="text-sm text-gray-700">
                        {authWindow && !authWindow.closed
                            ? 'Er is een nieuw venster geopend waar je kunt inloggen met je Microsoft account. Autoriseer daar de toegang.'
                            : 'Klik op de knop hieronder om een nieuw venster te openen waar je kunt inloggen met je Microsoft account.'}
                    </p>
                    {authUrl && (
                        <div className="flex flex-col gap-2">
                            <Button
                                onClick={handleOpenWindow}
                                className="w-full"
                                variant="default"
                                disabled={!!authWindow && !authWindow.closed}
                            >
                                <ExternalLink className="h-4 w-4 mr-2" />
                                {authWindow && !authWindow.closed
                                    ? 'Autorisatie venster is geopend...'
                                    : 'Open autorisatie venster'}
                            </Button>
                            {authWindow && !authWindow.closed && (
                                <p className="text-xs text-gray-500 text-center">
                                    Sluit dit dialoogvenster niet totdat je de autorisatie hebt voltooid.
                                </p>
                            )}
                        </div>
                    )}
                </div>
            </DialogContent>
        </Dialog>
    );
}

