import datetime
import platform
import signal  # Dealing with Ctrl+C
import sys
import time
from argparse import ArgumentParser
import pprint
from typing import NamedTuple
from urllib.parse import urlparse

try:
    from elasticsearch import Elasticsearch
except:
    print(
        "ERROR: elasticsearch module not installed. Please run 'pip install elasticsearch'."
    )
    sys.exit(1)


class Options(NamedTuple):
    ESClient: Elasticsearch
    index: str
    doc_type: str


DEBUG = False


# Ctrl+C
def signal_handler(signal, frame):
    debug('Ctrl+C pressed!')
    sys.exit(0)


def debug(*args):
    if DEBUG:
        print("DEBUG: ", *args)


def tail(args):
    global DEBUG
    DEBUG = args.debug

    # --endpoint
    endpoint, ssl = normalize_endpoint(args.endpoint)
    # --type
    doc_type = args.type
    # -f --nonstop
    non_stop = args.nonstop
    # -n --docs
    docs = args.docs

    if args.index:
        index = args.index
    else:
        index = datetime.datetime.utcnow().strftime("logstash-%Y.%m.%d")

    # http://elasticsearch-py.readthedocs.io/en/master/
    es_args = {}
    if ssl:
        es_args["use_ssl"] = True
        # Workaround to make it work in AWS AMI Linux
        # Python in AWS fails to locate the CA to validate the ES SSL endpoint and we need to specify it
        # https://access.redhat.com/articles/2039753
        if platform.platform()[0:5] == 'Linux':
            es_args['ca_certs'] = '/etc/pki/tls/certs/ca-bundle.crt'
        es_args['verify_certs'] = args.verify_certs
    es = Elasticsearch([endpoint], **es_args)

    opts = Options(es, index, doc_type)
    if not es.ping():
        raise Exception("network error")
    if not es.indices.exists(index):
        raise Exception("index not exists")

    interval = 1  # seconds
    to_the_past = 10000  # milliseconds

    # # Get the latest event timestamp from the Index
    # latest_event_timestamp = get_latest_event_timestamp(opts)

    # print(latest_event_timestamp)
    # # Go 10 seconds to the past.
    # from_timestamp = latest_event_timestamp - to_the_past

    outputer = output()
    next(outputer)

    from_timestamp = int(time.time() * 1000)

    res = search_events(None, opts, docs, 'desc')

    if len(res) > 0:
        res.reverse()
        outputer.send(res)
        from_timestamp = res[-1]['sort'][0]

    if not non_stop:
        return

    while True:
        from_date_time = ms_to_iso8601(from_timestamp)

        res = search_events(from_date_time, opts)
        if len(res) > 0:
            outputer.send(res)
            from_timestamp = res[-1]['sort'][0]

        # Wait for Elasticsearch to index a bit more of stuff and Print meanwhile
        wait(interval)
    outputer.close()


def output():
    printer = printout('json')
    next(printer)
    while True:
        events = yield
        for e in events:
            printer.send(e['_source'])
    printer.close()


def printout(style='json'):
    pp = pprint.PrettyPrinter(indent=1, depth=1, width=250, compact=True)
    while True:
        msg = yield
        if style == 'kv':
            if isinstance(msg, dict):
                s = []
                for k, v in msg.items():
                    s.append(f'{k}={v}')
                print(' '.join(s))
            else:
                print(msg)
        else:
            pp.pprint(msg)


def normalize_endpoint(endpoint):
    u = urlparse(endpoint)
    if u.scheme == 'http' and u.port is None:
        u = u._replace(netloc=u.netloc + ":80")
    if u.scheme == "https" and u.port is None:
        u = u._replace(netloc=u.netloc + ":443")

    return u.geturl(), u.scheme == "https"


# From timestamp in milliseconds to Elasticsearch format (seconds.milliseconds). i.e: 2016-07-14T13:37:45.123Z
def ms_to_iso8601(ms):
    return datetime.datetime.utcfromtimestamp(
        float(ms) / 1000).isoformat(timespec='milliseconds') + 'Z'


def get_latest_event_timestamp(opts):
    res = opts.ESClient.search(size=1,
                               index=opts.index,
                               doc_type=opts.doc_type,
                               _source=False,
                               sort="@timestamp:desc")

    print(res)
    if len(res['hits']['hits']) != 0:
        timestamp = res['hits']['hits'][0]['sort'][0]
        debug(f'get latest event timestamp : {timestamp}')
        return timestamp
    else:
        raise Exception(
            f'get_latest_event_timestamp: No results found with the current search criteria under index={index}'
        )


def search_events(from_date_time=None, opts={}, size=10000, order="asc"):
    debug("search_events: from_date_time:", from_date_time, size)
    # Mutable query object base for main search
    query_search = {
        "query": {
            "bool": {
                "must_not": {
                    "prefix": {
                        "agent.keyword":
                        "elasticsearch-py/"  # exclude self request if nginx logs exists
                    }
                }
            }
        }
    }

    if from_date_time is not None:
        query_search['query']['bool']['filter'] = {
            "range": {
                "@timestamp": {
                    "gt": from_date_time
                }
            }
        }

    if size is None:
        size = 10000

    res = opts.ESClient.search(size=size,
                               index=opts.index,
                               doc_type=opts.doc_type,
                               sort=f"@timestamp:{order}",
                               body=query_search)

    hits = res['hits']['hits']

    return hits


def wait(sec):
    time.sleep(sec)


def main():
    parser = ArgumentParser(
        description='Unix like tail command for Elastisearch')
    parser.add_argument('-e',
                        '--endpoint',
                        help='ES endpoint URL.',
                        required=True)
    parser.add_argument('-t',
                        '--type',
                        help='Doc_Type: apache, java, tomcat,... ',
                        default='apache')
    parser.add_argument('-i',
                        '--index',
                        help='Index name. Default to "logstash-YYYY.MM.DD".')
    parser.add_argument('-f',
                        '--nonstop',
                        help='Non stop. Continuous tailing.',
                        action="store_true")
    parser.add_argument('-n',
                        '--docs',
                        help='Number of documents.',
                        type=int,
                        metavar="[0-100]",
                        choices=range(0, 10000),
                        default=10)
    parser.add_argument('--verify_certs',
                        help="Verify certificate",
                        action="store_true")
    parser.add_argument('-d', '--debug', help='Debug', action="store_true")
    args = parser.parse_args()

    # Ctrl+C handler
    signal.signal(signal.SIGINT, signal_handler)

    tail(args)


if __name__ == "__main__":
    main()