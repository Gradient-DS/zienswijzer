import { useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

/**
 * LoginPage follows Rijkshuisstijl (Dutch Government) design guidelines
 * - Clean, accessible form layout
 * - Clear visual hierarchy
 * - Proper error handling and feedback
 * - WCAG compliant design
 */
export default function LoginPage() {
    const [email, setEmail] = useState('');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [errors, setErrors] = useState<{
        email?: string;
        username?: string;
        password?: string;
        general?: string;
    }>({});

    const login = useAuthStore((state) => state.login);
    const navigate = useNavigate();

    const validateForm = (): boolean => {
        const newErrors: typeof errors = {};

        if (!email.trim()) {
            newErrors.email = 'E-mailadres is verplicht';
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            newErrors.email = 'Voer een geldig e-mailadres in';
        }

        if (!username.trim()) {
            newErrors.username = 'Gebruikersnaam is verplicht';
        } else if (username.trim().length < 3) {
            newErrors.username = 'Gebruikersnaam moet minimaal 3 tekens bevatten';
        }

        if (!password.trim()) {
            newErrors.password = 'Wachtwoord is verplicht';
        } else if (password.length < 6) {
            newErrors.password = 'Wachtwoord moet minimaal 6 tekens bevatten';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setErrors({});

        if (!validateForm()) {
            return;
        }

        setIsLoading(true);

        try {
            await new Promise((resolve) => setTimeout(resolve, 500));

            login(username, email);
            navigate('/home', { replace: true });
        } catch (err) {
            setErrors({ general: 'Inloggen mislukt. Probeer het opnieuw.' });
        } finally {
            setIsLoading(false);
        }
    };

    const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setEmail(e.target.value);
        if (errors.email) {
            setErrors((prev) => ({ ...prev, email: undefined }));
        }
    };

    const handleUsernameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setUsername(e.target.value);
        if (errors.username) {
            setErrors((prev) => ({ ...prev, username: undefined }));
        }
    };

    const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setPassword(e.target.value);
        if (errors.password) {
            setErrors((prev) => ({ ...prev, password: undefined }));
        }
    };

    return (
        <Card className="w-full border-2 shadow-lg">
            <CardHeader className="pb-6">
                <CardTitle className="text-2xl font-semibold text-center text-foreground">
                    Welkom bij WOO Zienswijze
                </CardTitle>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleSubmit} noValidate>
                    <div className="mb-2">
                        <Label htmlFor="email" className="text-base font-medium block">
                            E-mailadres
                        </Label>
                        <Input
                            id="email"
                            type="email"
                            placeholder="naam@voorbeeld.nl"
                            value={email}
                            onChange={handleEmailChange}
                            required
                            disabled={isLoading}
                            aria-describedby="email-error"
                            aria-invalid={errors.email ? "true" : "false"}
                            className="h-11 my-1"
                        />
                        <p
                            id="email-error"
                            className={`text-sm text-destructive min-h-[1.25rem] ${errors.email ? 'visible' : 'invisible'}`}
                            role="alert"
                            aria-live="polite"
                        >
                            {errors.email || '\u00A0'}
                        </p>
                    </div>

                    <div className="mb-2">
                        <Label htmlFor="username" className="text-base font-medium block">
                            Gebruikersnaam
                        </Label>
                        <Input
                            id="username"
                            type="text"
                            placeholder="gebruikersnaam"
                            value={username}
                            onChange={handleUsernameChange}
                            required
                            disabled={isLoading}
                            aria-describedby="username-error"
                            aria-invalid={errors.username ? "true" : "false"}
                            className="h-11 my-1"
                        />
                        <p
                            id="username-error"
                            className={`text-sm text-destructive min-h-[1.25rem] ${errors.username ? 'visible' : 'invisible'}`}
                            role="alert"
                            aria-live="polite"
                        >
                            {errors.username || '\u00A0'}
                        </p>
                    </div>

                    <div className="mb-2">
                        <Label htmlFor="password" className="text-base font-medium block">
                            Wachtwoord
                        </Label>
                        <Input
                            id="password"
                            type="password"
                            placeholder="••••••••"
                            value={password}
                            onChange={handlePasswordChange}
                            required
                            disabled={isLoading}
                            aria-describedby="password-error"
                            aria-invalid={errors.password ? "true" : "false"}
                            className="h-11 my-1"
                        />
                        <p
                            id="password-error"
                            className={`text-sm text-destructive min-h-[1.25rem] ${errors.password ? 'visible' : 'invisible'}`}
                            role="alert"
                            aria-live="polite"
                        >
                            {errors.password || '\u00A0'}
                        </p>
                    </div>

                    <div
                        id="error-message"
                        role="alert"
                        className={`p-4 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-sm min-h-[3rem] ${errors.general ? 'visible' : 'invisible'}`}
                        aria-live="polite"
                    >
                        {errors.general || '\u00A0'}
                    </div>

                    <Button
                        type="submit"
                        className="w-full h-11 text-base font-medium"
                        disabled={isLoading}
                        aria-busy={isLoading}
                    >
                        {isLoading ? 'Inloggen...' : 'Inloggen'}
                    </Button>
                </form>
            </CardContent>
        </Card>
    );
}

