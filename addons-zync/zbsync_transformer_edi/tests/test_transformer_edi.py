# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo.addons.zbsync.tests.test_pipe import ZBSPipelineCase


class Unittest(ZBSPipelineCase):
    def test_edi_transformer(self):
        # TODO IMPLEMENT TEST
        data = """ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *200708*1838*U*00401*000000001*0*T*>
                    GS*IN*SENDER*RECEIVER*20200708*1838*1*X*004010
                    ST*810*000000001
                    BIG*20200708*INV-123456**PO19017369
                    N1*SF*WIDGETS LIMITED*92*123456789
                    N1*ST*ABC STORE 2257*92*2257
                    DTM*011*20200707
                    IT1*1*20*EA*6.12**UP*888519336892*CB*939393*VN*W2468
                    PID*F****WIDGET 12x2
                    IT1*2*10*EA*5.1**UP*888519393598*CB*182476*VN*W8275
                    PID*F****WIDGET 8x8
                    TDS*19757
                    SAC*C*D240***2417
                    CTT*2
                    SE*13*000000001
                    GE*1*1
                    IEA*1*000000001"""
