#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import base64
import hashlib
import sys

import six
from kafka import KafkaConsumer, KafkaProducer
from six import iteritems

if sys.platform == "win32":
    bootstrap_servers_list = ["node1:19092", "node2:19092", "node3:19092"]
elif sys.platform == "darwin":
    bootstrap_servers_list = ["node1:19092", "node2:19092", "node3:19092"]
else:
    bootstrap_servers_list = ["node1:19092", "node2:19092", "node3:19092"]


class UnknownTopicError(Exception):
    pass


class KafkaTopic(object):
    def __init__(self, bootstrap_servers, topic, validate_topic=True):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        if validate_topic:
            self._validate_topic()

    def _validate_topic(self):
        known_topics = self._get_topic_list()
        if self.topic not in known_topics:
            raise UnknownTopicError(
                "Topic %r does not exist. Known topics: %r" % (self.topic, known_topics)
            )

    def _get_topic_list(self):
        """ Return a list of all Kafka topics """
        consumer = self._get_consumer()

        def get_topics():
            return consumer.topics()

        try:
            return get_topics()
        finally:
            consumer.close()

    def _get_consumer(self):
        return KafkaConsumer(bootstrap_servers=self.bootstrap_servers)


class KafkaTopicWriter(KafkaTopic):
    """
        Kafka Writer which puts objects to a Kafka topic.
    """

    KAFKA_PRODUCER_CLOSE_TIMEOUT = 10

    def __init__(
            self,
            bootstrap_servers,
            topic,
            validate_topic=True,
            batch_size=1000,
            compression_type="gzip",
            **kwargs
    ):
        super(KafkaTopicWriter, self).__init__(bootstrap_servers, topic, validate_topic)
        _kwargs = {
            "retry_backoff_ms": 30000,  # unlimited retries by default
            "batch_size": batch_size,
            "max_request_size": 10 * 1024 * 1024,
            "request_timeout_ms": 120000,
            "compression_type": compression_type,
        }
        _kwargs.update(bootstrap_servers=bootstrap_servers)
        _kwargs.update(kwargs)
        self.producer = self._producer(**_kwargs)

    def sendjsondata(self, message):
        self.write(message)

    def write(self, msg=""):
        return self._send_message(self.topic, utf8(msg))

    def _producer(self, **kwargs):
        return KafkaProducer(**kwargs)

    def _send_message(self, topic, msg):
        self.producer.send(topic=topic, value=msg)
        self.producer.flush()
        return True

    def close(self):
        self.producer.flush(timeout=self.KAFKA_PRODUCER_CLOSE_TIMEOUT)
        self.producer.close(timeout=self.KAFKA_PRODUCER_CLOSE_TIMEOUT)


class KafkaTopicReader(KafkaTopic):
    """
        Kafka Writer which gets objects from a Kafka topic.
        {'smallest': 'earliest', 'largest': 'latest'}
    """

    def __init__(self, bootstrap_servers, topic, group_id, validate_topic=True, auto_offset_reset='earliest',
                 max_records=1000, **kwargs):
        super(KafkaTopicReader, self).__init__(bootstrap_servers, topic, validate_topic)
        self.max_records = max_records
        _kwargs = {
            'auto_offset_reset': auto_offset_reset,
            'consumer_timeout_ms': 120000,
            'group_id': group_id,
        }
        _kwargs.update(bootstrap_servers=bootstrap_servers)
        _kwargs.update(kwargs)
        self.consumer = self._consumer(**_kwargs)

    def _consumer(self, **kwargs):
        consumer = KafkaConsumer(**kwargs)
        consumer.subscribe([self.topic])
        return consumer

    def read(self):
        for msg in self._handle_read():
            yield msg

    def close(self):
        self.consumer.close()

    def _handle_read(self):
        """
        Read messages from Kafka.
        """

        while True:
            msgs = self.consumer.poll(timeout_ms=1000, max_records=self.max_records)
            for partition, msgs in msgs.iteritems():
                for msg in msgs:
                    yield msg


def md5string(x):
    return hashlib.md5(utf8(x)).hexdigest()


def utf8(string):
    """
    Make sure string is utf8 encoded bytes.

    If parameter is a object, object.__str__ will been called before encode as bytes
    """
    if isinstance(string, six.text_type):
        return string.encode("utf8")
    elif isinstance(string, six.binary_type):
        return string
    else:
        return six.text_type(string).encode("utf8")


def text(string, encoding="utf8"):
    """
    Make sure string is unicode type, decode with given encoding if it's not.

    If parameter is a object, object.__str__ will been called
    """
    if isinstance(string, six.text_type):
        return string
    elif isinstance(string, six.binary_type):
        return string.decode(encoding)
    else:
        return six.text_type(string)


def pretty_unicode(string):
    """
    Make sure string is unicode, try to decode with utf8, or unicode escaped string if failed.
    """
    if isinstance(string, six.text_type):
        return string
    try:
        return string.decode("utf8")
    except UnicodeDecodeError:
        return string.decode("Latin-1").encode("unicode_escape").decode("utf8")


def unicode_string(string):
    """
    Make sure string is unicode, try to default with utf8, or base64 if failed.

    can been decode by `decode_unicode_string`
    """
    if isinstance(string, six.text_type):
        return string
    try:
        return string.decode("utf8")
    except UnicodeDecodeError:
        return "[BASE64-DATA]" + base64.b64encode(string) + "[/BASE64-DATA]"


def unicode_dict(_dict):
    """
    Make sure keys and values of dict is unicode.
    """
    r = {}
    for k, v in iteritems(_dict):
        r[unicode_obj(k)] = unicode_obj(v)
    return r


def unicode_list(_list):
    """
    Make sure every element in list is unicode. bytes will encode in base64
    """
    return [unicode_obj(x) for x in _list]


def unicode_obj(obj):
    """
    Make sure keys and values of dict/list/tuple is unicode. bytes will encode in base64.

    Can been decode by `decode_unicode_obj`
    """
    if isinstance(obj, dict):
        return unicode_dict(obj)
    elif isinstance(obj, (list, tuple)):
        return unicode_list(obj)
    elif isinstance(obj, six.string_types):
        return unicode_string(obj)
    elif isinstance(obj, (int, float)):
        return obj
    elif obj is None:
        return obj
    else:
        try:
            return text(obj)
        except:
            return text(repr(obj))


def decode_unicode_string(string):
    """
    Decode string encoded by `unicode_string`
    """
    if string.startswith("[BASE64-DATA]") and string.endswith("[/BASE64-DATA]"):
        return base64.b64decode(string[len("[BASE64-DATA]"): -len("[/BASE64-DATA]")])
    return string


def decode_unicode_obj(obj):
    """
    Decode unicoded dict/list/tuple encoded by `unicode_obj`
    """
    if isinstance(obj, dict):
        r = {}
        for k, v in iteritems(obj):
            r[decode_unicode_string(k)] = decode_unicode_obj(v)
        return r
    elif isinstance(obj, six.string_types):
        return decode_unicode_string(obj)
    elif isinstance(obj, (list, tuple)):
        return [decode_unicode_obj(x) for x in obj]
    else:
        return obj
