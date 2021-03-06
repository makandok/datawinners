import unittest
from datetime import datetime
from collections import OrderedDict
from datawinners.custom_reports.crs.handler import CRSCustomReportHandler
from datawinners.custom_reports.crs.models import WayBillSent, WayBillReceived

class TestWayBillSent(unittest.TestCase):
    def setUp(self):
        self.way_bill_sent = None
        self.question_code = 'way1'
        self.data_record_id = 'data_rec_id'

    def tearDown(self):
        if self.way_bill_sent is not None:
            self.way_bill_sent.delete()

    def test_should_create_WayBillSent_from_submission_data(self):
        sent_date = datetime.strptime('11.11.2011', '%d.%m.%Y')
        waybill_sent_submission_data = OrderedDict(
            [('q7', u'pac1'), ('q18', u'2'), ('q4', sent_date), ('q3',u'sender_name'),
                ('q8', u'Transfer'), ('q2', u'2'), ('q17', u'9'), ('q9', u'Oil'), ('q15', 400), ('q6', 'receiver_code')])
        crs_custom_report_handler = CRSCustomReportHandler()
        crs_custom_report_handler.handle(self.question_code, waybill_sent_submission_data,self.data_record_id)
        self.way_bill_sent = WayBillSent.objects.filter(q1='pac1')[0]
        self.assertEquals('2', self.way_bill_sent.q2)
        self.assertEquals(datetime.date(sent_date), self.way_bill_sent.q3)
        self.assertEquals('Transfer', self.way_bill_sent.q4)
        self.assertEquals('2', self.way_bill_sent.q5)
        self.assertEquals('sender_name', self.way_bill_sent.q6)
        self.assertEquals('9', self.way_bill_sent.q7)
        self.assertEquals('Oil', self.way_bill_sent.q8)
        self.assertEquals(400, self.way_bill_sent.q9)
        self.assertEquals('receiver_code', self.way_bill_sent.q10)


class TestWayBillReceived(unittest.TestCase):
    def setUp(self):
        self.way_bill_received= None
        self.question_code = '002'
        self.data_record_id = 'data_rec_id'

    def tearDown(self):
        if self.way_bill_received is not None:
            self.way_bill_received.delete()

    def test_should_create_WayBillReceived_from_submission_data(self):
        received_date = datetime.strptime('11.11.2011', '%d.%m.%Y')
        waybill_received_submission_data = OrderedDict(
            [('q2', u'pac1'), ('q1', u'2'), ('q5', u'3'), ('q3', received_date),
                ('q6', u'receiver_name'), ('q7', u'2'), ('q13', 3), ('q15', 4)])
        crs_custom_report_handler = CRSCustomReportHandler()
        crs_custom_report_handler.handle(self.question_code, waybill_received_submission_data,self.data_record_id)
        self.way_bill_received = WayBillReceived.objects.get(q1='pac1')
        self.assertEquals('2', self.way_bill_received.q2)
        self.assertEquals('3', self.way_bill_received.q3)
        self.assertEquals('receiver_name', self.way_bill_received.q4)
        self.assertEquals(datetime.date(received_date), self.way_bill_received.q5)
        self.assertEquals('2', self.way_bill_received.q6)
        self.assertEquals(3, self.way_bill_received.q7)
        self.assertEquals(4, self.way_bill_received.q8)
