export function connectPlanejamentoWS(
  planejamentoId: string,
  onMessage: (data: any) => void
): WebSocket {
  // Fix #14: Use current host for WebSocket (works through nginx proxy)
  const API_URL = import.meta.env.VITE_API_URL || '';
  let wsUrl: string;
  if (API_URL) {
    wsUrl = API_URL.replace(/^http/, 'ws');
  } else {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    wsUrl = `${proto}//${window.location.host}`;
  }
  const ws = new WebSocket(`${wsUrl}/ws/planejamento/${planejamentoId}`);

  ws.onmessage = (event) => {
    onMessage(JSON.parse(event.data));
  };

  return ws;
}
