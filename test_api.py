import httpx
import time

# POST to image endpoint
with open('test_face.jpg', 'rb') as f:
    r = httpx.post(
        'http://127.0.0.1:8000/api/v1/analyze/image',
        files={'file': ('test_face.jpg', f, 'image/jpeg')},
        timeout=15
    )

print('POST status:', r.status_code)
data = r.json()
print('job_id:', data.get('job_id'))
print('status:', data.get('status'))
job_id = data.get('job_id')

# Poll for result
for i in range(15):
    time.sleep(2)
    r2 = httpx.get(f'http://127.0.0.1:8000/api/v1/analyze/result/{job_id}', timeout=10)
    result = r2.json()
    s = result.get('status')
    print(f'Poll {i+1}: status={s}')
    if s == 'done':
        d = result['data']
        print('score:', d.get('score'))
        print('verdict:', d.get('verdict'))
        ela = d.get('explainability', {}).get('ela_base64_heatmap_prefix', '')
        print('heatmap prefix:', ela[:60], ('...' if ela else '(empty)'))
        print('regions:', d.get('explainability', {}).get('regions'))
        break
    elif s == 'failed':
        print('FAILED:', result)
        break
