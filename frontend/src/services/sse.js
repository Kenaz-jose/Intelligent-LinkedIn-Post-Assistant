export const startOptimizationStream = async (payload, onEvent, onError, onComplete) => {
  try {
    const response = await fetch('/api/optimize/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error('Stream request failed');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      
      // Keep the last chunk in buffer if it's incomplete (doesn't end with \n\n)
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const dataStr = line.replace('data: ', '').trim();
          if (!dataStr) continue;
          
          try {
            const data = JSON.parse(dataStr);
            if (data.status === 'final') {
              onComplete(data.result);
            } else {
              onEvent(data);
            }
          } catch (e) {
            console.error('Error parsing SSE JSON chunk', e);
          }
        }
      }
    }
    
    // Process any remaining buffer just in case
    if (buffer.startsWith('data: ')) {
        const dataStr = buffer.replace('data: ', '').trim();
        if (dataStr) {
            try {
                const data = JSON.parse(dataStr);
                if (data.status === 'final') {
                    onComplete(data.result);
                } else {
                    onEvent(data);
                }
            } catch (e) {
                console.error('Error parsing SSE JSON chunk', e);
            }
        }
    }

  } catch (error) {
    onError(error);
  }
};

