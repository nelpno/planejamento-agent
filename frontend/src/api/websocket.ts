export function connectPlanejamentoWS(
  planejamentoId: string,
  onMessage: (data: any) => void
): WebSocket {
  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const wsUrl = API_URL.replace('http', 'ws');
  const ws = new WebSocket(`${wsUrl}/ws/planejamento/${planejamentoId}`);

  ws.onmessage = (event) => {
    onMessage(JSON.parse(event.data));
  };

  return ws;
}
