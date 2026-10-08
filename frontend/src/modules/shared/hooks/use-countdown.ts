import { useEffect, useState } from 'react';

function useCountdown(targetIso: string | null): number {
	const targetMs = targetIso ? new Date(targetIso).getTime() : null;

	const [remainingSeconds, setRemainingSeconds] = useState(() =>
		targetMs ? Math.max(Math.ceil((targetMs - Date.now()) / 1000), 0) : 0,
	);

	useEffect(() => {
		if (!targetMs) {
			setRemainingSeconds(0);
			return;
		}

		function tick() {
			setRemainingSeconds(
				Math.max(Math.ceil((targetMs! - Date.now()) / 1000), 0),
			);
		}

		tick();
		const interval = setInterval(tick, 1000);
		return () => clearInterval(interval);
	}, [targetMs]);

	return remainingSeconds;
}

export { useCountdown };
