"""Bounded CloudWatch Logs pagination for isolated Lambda invocation proof."""
from __future__ import annotations


def count_lambda_starts(client, log_group: str, start_ms: int, end_ms: int, *, max_pages: int = 20, max_events: int = 100) -> int:
    if (not isinstance(log_group, str) or not log_group.startswith('/aws/lambda/')
            or type(start_ms) is not int or type(end_ms) is not int or not 0 <= start_ms <= end_ms
            or not 1 <= max_pages <= 50 or not 1 <= max_events <= 500):
        raise ValueError('invalid bounded log proof request')
    token = None
    seen = set()
    events = 0
    for _ in range(max_pages):
        kwargs = {
            'logGroupName': log_group,
            'startTime': start_ms,
            'endTime': end_ms,
            'filterPattern': '"START RequestId:"',
            'limit': min(100, max_events - events),
        }
        if kwargs['limit'] <= 0:
            raise RuntimeError('log proof event ceiling reached')
        if token:
            kwargs['nextToken'] = token
        value = client.filter_log_events(**kwargs)
        page = value.get('events', [])
        if not isinstance(page, list) or len(page) > kwargs['limit']:
            raise RuntimeError('unexpected log proof page')
        events += len(page)
        next_token = value.get('nextToken')
        if not next_token:
            return events
        if next_token == token or next_token in seen:
            raise RuntimeError('repeated CloudWatch pagination token')
        seen.add(next_token)
        token = next_token
    raise RuntimeError('log proof page ceiling reached')
