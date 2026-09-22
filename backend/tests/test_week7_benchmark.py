import pytest
import httpx
from scripts.benchmark_http import percentile, run_baseline


@pytest.mark.parametrize("url", ["https://example.com", "http://user:secret@localhost:8000",
                                  "http://localhost:8000/api/v1/predict", "http://localhost:8000?x=y"])
def test_benchmark_refuses_nonlocal_or_nonroot_targets(url):
    with pytest.raises(ValueError):
        run_baseline(url, requests=1, concurrency=1, timeout=1)


@pytest.mark.parametrize("requests,concurrency,timeout", [(0,1,1),(6000,1,1),(1,33,1),(1,1,float('nan'))])
def test_benchmark_bounds(requests, concurrency, timeout):
    with pytest.raises(ValueError):
        run_baseline("http://localhost:8000", requests=requests, concurrency=concurrency, timeout=timeout)


def test_percentile_counts_timeouts_as_attempt_latency():
    assert percentile([], .95) is None
    assert percentile([1, 2, 3, 4, 1000], .95) == 1000
    assert percentile([1, 2, 3], .5) == 2


def test_http_errors_and_timeouts_are_counted(monkeypatch):
    from scripts import benchmark_http
    actual_client = httpx.Client
    calls = 0
    def handle(request):
        nonlocal calls
        calls += 1
        if calls <= 4:
            return httpx.Response(200)
        if calls % 2:
            raise httpx.ReadTimeout("synthetic timeout", request=request)
        return httpx.Response(503)
    monkeypatch.setattr(benchmark_http.httpx, "Client", lambda **kwargs: actual_client(
        **kwargs, transport=httpx.MockTransport(handle)))
    result = run_baseline("http://localhost:8000", requests=8, concurrency=1, timeout=1)
    assert result["results"] == {"timeout": 4, "503": 4}
    assert result["memory"]["sampled_peak_bytes"] is None
    assert result["warmup_requests_excluded"] == 4
