"""Fixed independent CRUD acceptance suite; generated code runs in another process."""
import json,os,subprocess,sys,time
import httpx
# The hardened snapshot makes /opt/company root-owned and non-writable to the coding user.
process=subprocess.Popen([sys.executable,'-m','uvicorn','app:app','--host','127.0.0.1','--port','8101'],cwd='/workspace/repo',env={'PATH':os.environ['PATH'],'HOME':'/home/daytona','DATABASE_PATH':'/workspace/benchmark.sqlite'})
try:
    client=httpx.Client(base_url='http://127.0.0.1:8101',timeout=3)
    for _ in range(50):
        try:
            if client.get('/health').status_code==200:break
        except httpx.HTTPError:pass
        time.sleep(.1)
    else:raise AssertionError('App did not start')
    item=client.post('/items',json={'name':'Verified CRUD item'});assert item.status_code==201,item.text
    record=item.json();assert record['name']=='Verified CRUD item'
    id=record['id'];assert client.get(f'/items/{id}').json()['name']==record['name']
    changed=client.patch(f'/items/{id}',json={'name':'Updated item'});assert changed.status_code==200
    assert any(i['id']==id for i in client.get('/items').json())
    process.terminate();process.wait(timeout=5)
    process=subprocess.Popen([sys.executable,'-m','uvicorn','app:app','--host','127.0.0.1','--port','8101'],cwd='/workspace/repo',env={'PATH':os.environ['PATH'],'HOME':'/home/daytona','DATABASE_PATH':'/workspace/benchmark.sqlite'})
    for _ in range(50):
        try:
            if client.get('/health').status_code==200:break
        except httpx.HTTPError:pass
        time.sleep(.1)
    assert client.get(f'/items/{id}').json()['name']=='Updated item','Persistence after process restart failed'
    assert client.delete(f'/items/{id}').status_code in {200,204}
    assert client.get(f'/items/{id}').status_code==404
    assert client.post('/items',json={'name':''}).status_code==422
    print(json.dumps({'suite':'crud-benchmark-v1','checks':8,'passed':True}))
finally:
    process.terminate();process.wait(timeout=5)
