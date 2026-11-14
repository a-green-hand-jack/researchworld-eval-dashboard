import unittest
import torch
from train import Net, dataset, first_event


class Checks(unittest.TestCase):
    def test_data(self):
        for op in ['add', 'sub']:
            x, y, tr, te = dataset(7, .5, 2, op)
            self.assertEqual(x.shape, (49, 14))
            self.assertEqual(len(set(tr.tolist()) & set(te.tolist())), 0)
            self.assertEqual(sorted(tr.tolist() + te.tolist()), list(range(49)))
            self.assertTrue(torch.equal(tr, dataset(7, .5, 2, op)[2]))
            self.assertEqual(y[3*7+5].item(), ((3+5) if op=='add' else (3-5)) % 7)
            self.assertTrue(torch.equal(x.sum(1), torch.full((49,), 2.)))

    def test_model(self):
        for act in ['relu', 'square']:
            m = Net(7, 16, act)
            self.assertEqual(sum(q.numel() for q in m.parameters()), 3*7*16)
            x,y,tr,_ = dataset(7,.5,1)
            torch.nn.functional.cross_entropy(m(x[tr]), y[tr]).backward()
            self.assertTrue(all(q.grad is not None for q in m.parameters()))

    def test_frozen(self):
        m=Net(7,16,frozen=True)
        x,y,tr,_=dataset(7,.5,1)
        before=m.hidden.weight.detach().clone()
        opt=torch.optim.AdamW([q for q in m.parameters() if q.requires_grad],lr=.01,weight_decay=1)
        torch.nn.functional.cross_entropy(m(x[tr]),y[tr]).backward()
        opt.step()
        self.assertTrue(torch.equal(before,m.hidden.weight))
        self.assertIsNone(m.hidden.weight.grad)

    def test_event(self):
        rows=[dict(step=i*100,acc=a) for i,a in enumerate([0,1,0,1,1,1,0])]
        self.assertEqual(first_event(rows,'acc',.99),300)
        self.assertIsNone(first_event(rows[:5],'acc',.99))

    def test_replay(self):
        x,_,_,_=dataset(7,.5,1)
        torch.manual_seed(10)
        a=Net(7,8)(x)
        torch.manual_seed(10)
        b=Net(7,8)(x)
        self.assertTrue(torch.equal(a,b))


if __name__=='__main__':
    torch.set_num_threads(1)
    unittest.main()
