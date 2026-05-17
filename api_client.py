import requests


class APIError(Exception):
    pass


class APIClient:
    def __init__(self, config):
        self.config = config

    def _headers(self):
        return {
            'Authorization': f'Bearer {self.config.api_key}',
            'Content-Type': 'application/json',
            'X-Title': 'newsfeed',
        }

    def complete(self, messages, system=None):
        if not self.config.api_key:
            raise APIError("No API key configured.")
        payload = {'model': self.config.model, 'messages': messages}
        if system:
            payload['messages'] = [{'role': 'system', 'content': system}] + list(messages)
        try:
            resp = requests.post(
                f"{self.config.base_url.rstrip('/')}/chat/completions",
                headers=self._headers(),
                json=payload,
                timeout=120,
            )
            resp.raise_for_status()
            return resp.json()['choices'][0]['message']['content']
        except requests.HTTPError as e:
            try:
                detail = e.response.json().get('error', {}).get('message', str(e))
            except Exception:
                detail = str(e)
            raise APIError(f"API error: {detail}")
        except requests.RequestException as e:
            raise APIError(f"Network error: {e}")
