# TailEs - Tail for ElasticSearch

## Usage

```sh
python3 tailes.py -e "http://elastic:password@127.0.0.1:9200" -i "nginx-2020.04" -t "flb_type" -f
```

KV-style: `--format kv`

```
> python3 tailes.py -e "http://elastic:password@127.0.0.1:9200" -i "nginx-2020.04" -t "flb_type" -f --format kv
@timestamp=2020-04-17T08:51:16.000Z remote=1.2.3.4 host=- user=- method=POST path=/-/npm/v1/security/audits/quick code=200 size=23744 referer=install agent=npm/6.14.4 node/v10.7.0 linux x64 ci/jenkins
@timestamp=2020-04-17T08:51:19.000Z remote=1.2.3.4 host=- user=- method=GET path=/ code=200 size=77 referer=https://example.com/ agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:75.0) Gecko/20100101 Firefox/75.0
```

JSON-style: `--format json`

```
> python3 tailes.py -e "http://elastic:password@127.0.0.1:9200" -i "nginx-2020.04" -t "flb_type" -f --format kv
{'@timestamp': '2020-04-17T08:51:24.000Z',
 'agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:75.0) Gecko/20100101 Firefox/75.0',
 'code': '200',
 'host': '-',
 'method': 'GET',
 'path': '/',
 'referer': 'https://example.com/',
 'remote': '1.2.3.4',
 'size': '77',
 'user': '-'}
{'@timestamp': '2020-04-17T08:51:29.000Z',
 'agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:75.0) Gecko/20100101 Firefox/75.0',
 'code': '200',
 'host': '-',
 'method': 'POST',
 'path': '/login',
 'referer': 'https://example.com/',
 'remote': '1.2.3.4',
 'size': '77',
 'user': '-'}
```
