// Puente entre `api-client.ts` (corre fuera del árbol de React, como
// interceptor de fetch) y `AuthProvider`: no puede llamar `useAuth().clear()`
// directamente, así que dispara un evento en `window` en vez de depender de
// una referencia de función guardada en una variable de módulo — `window`
// sobrevive a cualquier reevaluación de este módulo por HMR, a diferencia de
// esa variable.
const SESSION_CLEARED_EVENT = 'trading-app:session-cleared';

function dispatchSessionCleared() {
	window.dispatchEvent(new Event(SESSION_CLEARED_EVENT));
}

function onSessionCleared(listener: () => void): () => void {
	window.addEventListener(SESSION_CLEARED_EVENT, listener);
	return () => window.removeEventListener(SESSION_CLEARED_EVENT, listener);
}

export { dispatchSessionCleared, onSessionCleared };
