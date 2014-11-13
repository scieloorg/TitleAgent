# coding: utf-8
import zerorpc

class ArticleMetaRPCClient(object):

    def __init__(self, server='tcp://192.168.169.148:4242'):
        self.c = zerorpc.Client(heartbeat=None)
        self.c.connect(server)

    def add_journal(self, metadata):

        print self.c.add_journal(metadata)