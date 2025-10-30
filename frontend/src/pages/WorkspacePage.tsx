import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

export default function WorkspacePage() {
    const [isLoading, setIsLoading] = useState(false);
    const { username, email, logout } = useAuthStore();
    const navigate = useNavigate();

    const handleLogout = async () => {
        setIsLoading(true);

        try {
            await new Promise((resolve) => setTimeout(resolve, 500));
            logout();
            navigate('/login', { replace: true });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white p-6">
            <div className="max-w-4xl mx-auto space-y-6">
                <div className="text-center space-y-2">
                    <h1 className="text-4xl font-bold text-gray-900">
                        Welcome to Your Workspace
                    </h1>
                    <p className="text-gray-600">
                        You're successfully logged in
                    </p>
                </div>

                <Card>
                    <CardHeader>
                        <CardTitle>User Information</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div>
                            <p className="text-sm font-semibold text-gray-600">Username</p>
                            <p className="text-lg text-gray-900">{username}</p>
                        </div>

                        <div>
                            <p className="text-sm font-semibold text-gray-600">Email</p>
                            <p className="text-lg text-gray-900">{email}</p>
                        </div>

                        <div className="pt-4 border-t">
                            <Button
                                onClick={handleLogout}
                                variant="destructive"
                                disabled={isLoading}
                                className="w-full"
                            >
                                {isLoading ? 'Signing out...' : 'Sign Out'}
                            </Button>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="pt-6">
                        <p className="text-sm text-gray-600 text-center">
                            This is a basic workspace page. More features will be added soon.
                        </p>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}

