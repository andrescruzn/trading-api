import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider } from '@tanstack/react-router';
import { AuthProvider } from '@/modules/auth/context/auth-provider';
import { Toaster } from './modules/ui/components/toast';
import { TooltipProvider } from './modules/ui/components/tooltip';
import { router } from './router';

const queryClient = new QueryClient();

export function App() {
	return (
		<QueryClientProvider client={queryClient}>
			<AuthProvider>
				<TooltipProvider>
					<RouterProvider router={router} />
					<Toaster limit={1} />
				</TooltipProvider>
			</AuthProvider>
		</QueryClientProvider>
	);
}
