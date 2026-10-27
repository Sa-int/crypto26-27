"""Offline correctness and negative-input regression tests for lab4.py."""
import json
import random
import re
import unittest
from pathlib import Path

import lab4 as rsa


class RSALab4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sample = rsa.load_sample()
        cls.pub_a, cls.prv_a = rsa.GenerateKeyPair(cls.sample['p'], cls.sample['q'])
        cls.pub_b, cls.prv_b = rsa.GenerateKeyPair(cls.sample['p1'], cls.sample['q1'])
        cls.server_text = (Path(__file__).resolve().parent / 'server_check.txt').read_text(encoding='utf-8')

    def test_horner_matches_builtin_pow(self):
        r = random.Random(42)
        for _ in range(150):
            base = r.randrange(0, 100_000)
            exp = r.randrange(0, 1000)
            mod = r.randrange(1, 9999)
            self.assertEqual(rsa.mod_pow(base, exp, mod), pow(base, exp, mod))

    def test_gcd_extended_and_inverse(self):
        for a, b in [(16, 7), (65537, 3120), (7, 40), (37, 1000)]:
            g, u, v = rsa.egcd(a, b)
            self.assertEqual(a*u + b*v, g)
            if g == 1:
                self.assertEqual(a*rsa.inverse(a, b) % b, 1)

    def test_small_primes_and_rejections(self):
        self.assertEqual(len(rsa.SMALL_PRIMES), 168)
        expected = {'p': (36, 7), 'q': (41, 12), 'p1': (15, 1), 'q1': (39, 10)}
        for name, counts in expected.items():
            records = rsa.recreate_candidates(self.sample[name], self.sample['rejected_count'][name])
            trial = sum(not reason.startswith('Miller') for _, reason in records)
            mr = len(records) - trial
            self.assertEqual((trial, mr), counts)

    def test_mr_prime_examples_and_actual_base(self):
        primes, _, log, _ = rsa.create_parameters(sample=True)
        for name, n in primes.items():
            self.assertEqual(n.bit_length(), 256)
            self.assertEqual(len(log[name]), 20)
            self.assertEqual(len(set(log[name])), 20)
            self.assertTrue(rsa.miller_rabin(n, rng=random.Random(1717)))
        self.assertEqual(log['p1'][0], self.sample['trace_base'])
        trace = rsa.miller_rabin_trace(primes['p1'], log['p1'][0])
        self.assertIn('r=1', '\n'.join(trace))
        self.assertIn('this round PASSED', trace[-1])

    def test_composites_and_small_numbers(self):
        for n in (0, 1, 4, 6, 9, 15, 21, 341, 561, 1105, 1729, 2047):
            self.assertFalse(rsa.miller_rabin(n, rng=random.Random(40)), n)
        for n in (2, 3, 5, 7, 11, 101, 1009):
            self.assertTrue(rsa.miller_rabin(n, rng=random.Random(40)), n)

    def test_key_invariants_and_invalid_inputs(self):
        for pub, prv in ((self.pub_a,self.prv_a),(self.pub_b,self.prv_b)):
            n, e = pub
            d, p, q = prv
            self.assertNotEqual(p,q)
            self.assertEqual(n,p*q)
            self.assertEqual(rsa.gcd(e,(p-1)*(q-1)),1)
            self.assertEqual(e*d%((p-1)*(q-1)),1)
            self.assertEqual(n.bit_length(),512)
        with self.assertRaises(ValueError):
            rsa.GenerateKeyPair(101,101)
        with self.assertRaises(ValueError):
            rsa.GenerateKeyPair(3,7,e=6)
        with self.assertRaises(ValueError):
            rsa.Encrypt(self.pub_a[0],self.pub_a)
        with self.assertRaises(ValueError):
            rsa.Decrypt(-1,self.prv_a)
        with self.assertRaises(ValueError):
            rsa.Sign(-1,self.prv_a)

    def test_two_parties_encrypt_sign(self):
        for name,pub,prv in (('A',self.pub_a,self.prv_a),('B',self.pub_b,self.prv_b)):
            m=self.sample['M_'+name]
            c=rsa.Encrypt(m,pub)
            self.assertEqual(rsa.Decrypt(c,prv),m)
            _,s=rsa.Sign(m,prv)
            self.assertTrue(rsa.Verify(m,s,pub))
            self.assertFalse(rsa.Verify(m+1,s,pub))
            self.assertFalse(rsa.Verify(m,pub[0],pub))
            self.assertFalse(rsa.Verify(m,-1,pub))

    def test_send_receive_and_invalid_key_rejection(self):
        k = self.sample['k']
        k1, s1 = rsa.SendKey(k,self.prv_a,self.pub_b)
        self.assertEqual(rsa.ReceiveKey(k1,s1,self.prv_b,self.pub_a),
                         (k,rsa.Sign(k,self.prv_a)[1],True))
        for invalid in (0,-1,self.pub_a[0]):
            with self.assertRaises(ValueError):
                rsa.SendKey(invalid,self.prv_a,self.pub_b)
        with self.assertRaises(ValueError):
            rsa.SendKey(k,self.prv_b,self.pub_a)
        for bad in ((self.pub_b[0],s1),(-1,s1),(k1,-1),(k1,self.pub_b[0])):
            self.assertEqual(rsa.ReceiveKey(*bad,self.prv_b,self.pub_a),(None,None,False))
        self.assertEqual(rsa.ReceiveKey(k1,(s1+1)%self.pub_b[0],self.prv_b,self.pub_a),
                         (None,None,False))
        self.assertEqual(rsa.ReceiveKey(k1,s1,self.prv_b,self.pub_b),
                         (None,None,False))
        # Deliberately encrypted zero with matching RSA signature 0: must reject.
        self.assertEqual(rsa.ReceiveKey(0,0,self.prv_b,self.pub_a),(None,None,False))

    def test_original_interoperability_examples_offline(self):
        text=self.server_text
        def parse(label):
            m=re.search(r'^'+re.escape(label)+r'\s*=\s*([0-9A-F]+)',text,re.M)
            self.assertIsNotNone(m,label)
            return int(m.group(1),16)
        server_n=parse('Ключ сервера (512 біт): n_s')
        server_e=65537
        # Server encrypted for our local public key.
        server_m=int('4C6162342046422D3433204B6F726F746B612054796D6368616B',16)
        server_c=int('5AA113726DDC020B0FE16617AC18FEDC46BDA75E300444D88C54DCD2A132A7749C21B39462DF89A92DB8B14F3F1F671F0042044E18DBEF14935889D1D1A77579',16)
        self.assertEqual(rsa.Decrypt(server_c,self.prv_a),server_m)
        # Our encryption for server matches the value recorded with screenshots.
        to_server=int('52534120746573743A2046422D3433202D3E20736572766572',16)
        local_c=int('5EE93ED82CA5E587991CB06EEBF04DCE769261449D5A30E736C58AADB86812F979334C43D8EBA7E1332E1AF467B1614DC3B8C6E8FADF23CE0BFF337D533A59FB',16)
        self.assertEqual(rsa.Encrypt(to_server,(server_n,server_e)),local_c)
        # Server signature verified with server public key, and our signature
        # coincides with the historical value verified by the server.
        signed_by_server=int('5369676E6564206279207365727665722C20636865636B65642062792046423433',16)
        server_signature=int('0561830D9CF31239BAEAF7940B7446EE30C0C79DE4D0983871A470B5F6BABDF6E3380C1458779D0539A5616E4A751EA416B6546DBD8E286A7031776176BC571F',16)
        self.assertTrue(rsa.Verify(signed_by_server,server_signature,(server_n,server_e)))
        signed_by_us=int('5369676E65642062792046422D34332C20636865636B656420627920736572766572',16)
        our_signature=int('1951186AD4F9190062ACAEEF436190E03DEBEA7A164DE8D8A8641179F61A5F7580643AA17DCF63808FBD8D1314E2952948145CBF4763EF79DDB33E97FE47605B',16)
        self.assertEqual(rsa.Sign(signed_by_us,self.prv_a)[1],our_signature)
        incoming_k1=int('B43F9DF1FB01B613A5EDEC9F30E777C035A2A46B368EA1B2C38FAFD5D304947018177F068D2898A6EA219A756BAAE6BF772A0A1D5AB55CA4E1315DCDE4E56885',16)
        incoming_s1=int('158D453654FA0BBD8C3235150CF908D3E733A80B8E4E8B530C512A09D8D49ED498BC4201E653BD1B548BF22CE37780097D50B8B9918EC4D69BF2CEB2D7FD19DA',16)
        got,_,valid=rsa.ReceiveKey(incoming_k1,incoming_s1,self.prv_a,(server_n,server_e))
        self.assertTrue(valid)
        self.assertEqual(got,int('DC4E3CB8E111DF95',16))
        server_1024=parse('n_s (1024)')
        k=int('1633EF988208DB42082802F3087DE3C9',16)
        c,s=rsa.SendKey(k,self.prv_a,(server_1024,server_e))
        self.assertEqual(c,int('78A66E4EA1F54BA3F4F4768F2E88385759E83E4E98CDE4527A94AD281C25341B17702E2A14056C1A42B6D333354C412D2D1C22FCA499AFC59CC1E35278D3B7842606F183FA6919AA786F3AA4480C738FA4D5AB377D1519BC122C3AF4BCCBEE0CBE7A25159FF41EB20C308CA1F7F73551AD1C144D535AC03C89DEDDBD38453F93',16))
        self.assertEqual(s,int('2907742AC723EBC532BE6A115BD3C291FB078DCB8E81C017637EA6B3032CC0F971FF12F584100417F95B6F6F08691E61C52178950C707D5CCD800B1D957DD2D4F9BA6EDBC848FD89E8ED7EEA63DCA244DA27279CB4C69685332CD4898B189533AB9CAAA38A034D5D166AD3D131157AB5B98F1B3CAC24D1B9C649B9F8E6B1306E',16))


if __name__ == '__main__':
    unittest.main()
