export default function NotFoundPage() {
    return (
        <div className="min-h-screen flex items-center justify-center bg-background">
            <div className="text-center space-y-4">
                <h1 className="text-6xl font-bold text-gray-900">404</h1>
                <p className="text-xl text-gray-600">Page not found</p>
                <a
                    href="/"
                    className="inline-block text-primary hover:underline"
                >
                    Go back home
                </a>
            </div>
        </div>
    );
}

