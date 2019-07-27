import torch
import torch.nn as nn
from parameters import *


torch.manual_seed(1)
CUDA = torch.cuda.is_available()


class lstm_crf(nn.Module):
    def __init__(self, vocab_size, num_tags):
        super().__init__()
        self.lstm = lstm(vocab_size, num_tags)    # Bi-LSTM
        self.crf = crf(num_tags)            #  CRF
        self = self.cuda() if CUDA else self

    def forward(self, x, y):  # for training
        mask = x.data.gt(0).float()   #  tensor每个位置，数值大于零就是1， 反之就是0
        h = self.lstm(x, mask)
        Z = self.crf.forward(h, mask)   #  预测得分
        score = self.crf.score(h, y, mask)    #  计算给定序列的得分
        return Z - score  # NLL loss

    def decode(self, x):  # for prediction
        mask = x.data.gt(0).float()
        h = self.lstm(x, mask)
        return self.crf.decode(h, mask)


class lstm(nn.Module):
    def __init__(self, vocab_size, num_tags):
        super().__init__()

        # architecture
        self.embed = nn.Embedding(vocab_size, EMBED_SIZE, padding_idx=PAD_IDX)
        self.lstm = nn.LSTM(
            input_size=EMBED_SIZE,     #  输入的特征维度，即词嵌入的输出维度
            hidden_size=HIDDEN_SIZE // NUM_DIRS,   #  隐藏层的特征维度/2
            num_layers=NUM_LAYERS,    #  网络层数
            bias=True,
            batch_first=True,    #  batch优先，(batch,seq,feature)
            dropout=DROPOUT,    #  除了最后一层外的其他输出层加上dropout层
            bidirectional=BIDIRECTIONAL    #  双向LSTM
        )
        self.out = nn.Linear(HIDDEN_SIZE, num_tags)  # 全连接层，输出维度是标签向量维度

    def init_hidden(self):   # 初始化隐藏层的状态
        h = zeros(NUM_LAYERS * NUM_DIRS, BATCH_SIZE, HIDDEN_SIZE // NUM_DIRS)  # h0 (layers*direction,batch,hidden)
        c = zeros(NUM_LAYERS * NUM_DIRS, BATCH_SIZE, HIDDEN_SIZE // NUM_DIRS)  # c0
        return (h, c)    # LSTM的输入是x，(h,c)

    def forward(self, x, mask):
        self.hidden = self.init_hidden()
        x = self.embed(x)      #  词嵌入，[B, L, dim_out]
        '''
        torch.nn.utils.rnn.pack_padded_sequence():将一个填充后的变长序列压紧
        输入x的形状可以是(T×B×* )。T是最长序列长度，B是batch size，*代表任意维度(可以是0)。如果batch_first=True的话，那么相应的 input size 就是 (B×T×*)。
        输入是变长序列x，和x中每个序列的长度
        返回的是一个PackedSequence 对象: （令牌的总数，每个令牌的维度）,每个时间步长的令牌数列表
        '''
        x = nn.utils.rnn.pack_padded_sequence(x, mask.sum(1).int(), batch_first=True)   #mask.sum(1)是每句话的长度
        h, _ = self.lstm(x, self.hidden)     #  _ 就是剔除padding字符后的hidden state和cell state
        '''
        nn.utils.rnn.pad_packed_sequence():把压紧的序列再填充回来。
        返回值是B×T×*。
        '''
        h, _ = nn.utils.rnn.pad_packed_sequence(h, batch_first=True)     # [B, L, hidden]
        h = self.out(h)      #  全连接,输出维度是标签向量维度  # [B, L, num_tags]
        h *= mask.unsqueeze(2)   # [B, L, num_tags] * [B, L, 1]
        return h


class crf(nn.Module):
    def __init__(self, num_tags):
        super().__init__()
        self.num_tags = num_tags

        self.trans = nn.Parameter(randn(num_tags, num_tags))    # torch.Size([num_tags, num_tags])  转移矩阵,每个值表示tag_j转移到tag_i的转移概率
        self.trans.data[SOS_IDX, :] = -10000.  # no transition to SOS
        self.trans.data[:, EOS_IDX] = -10000.  # no transition from EOS except to PAD
        self.trans.data[:, PAD_IDX] = -10000.  # no transition from PAD except to PAD
        self.trans.data[PAD_IDX, :] = -10000.  # no transition to PAD except from EOS
        self.trans.data[PAD_IDX, EOS_IDX] = 0.
        self.trans.data[PAD_IDX, PAD_IDX] = 0.

    def forward(self, h, mask):  # forward algorithm
        score = Tensor(BATCH_SIZE, self.num_tags).fill_(-10000.)  # torch.Size([BATCH_SIZE, num_tags])
        score[:, SOS_IDX] = 0.
        trans = self.trans.unsqueeze(0)  # [1, num_tags, num_tags]
        for t in range(h.size(1)):  # recursion through the sequence，h是发射矩阵，每个值代表词w_i映射到tag_j的非归一化概率
            mask_t = mask[:, t].unsqueeze(1)
            emit_t = h[:, t].unsqueeze(2)  # [BATCH_SIZE, num_tags, 1]
            score_t = score.unsqueeze(1) + emit_t + trans  # [BATCH_SIZE, 1, num_tags] -> [BATCH_SIZE, num_tags, num_tags]
            score_t = log_sum_exp(score_t)  # [BATCH_SIZE, num_tags, num_tags] -> [BATCH_SIZE, num_tags]
            score = score_t * mask_t + score * (1 - mask_t)
        score = log_sum_exp(score + self.trans[EOS_IDX])
        return score  # partition function

    def score(self, h, y, mask):  # calculate the score of a given sequence
        score = Tensor(BATCH_SIZE).fill_(0.)
        h = h.unsqueeze(3)
        trans = self.trans.unsqueeze(2)   # [num_tags, num_tags, 1]
        for t in range(h.size(1)):  # h.size(1): L
            mask_t = mask[:, t]
            emit_t = torch.cat([h[t, y[t + 1]] for h, y in zip(h, y)])
            trans_t = torch.cat([trans[y[t + 1], y[t]] for y in y])
            score += (emit_t + trans_t) * mask_t
        last_tag = y.gather(1, mask.sum(1).long().unsqueeze(1)).squeeze(1)
        score += self.trans[EOS_IDX, last_tag]
        return score

    def decode(self, h, mask):  # Viterbi 解码
        # initialize backpointers and viterbi variables in log space
        bptr = LongTensor()
        score = Tensor(BATCH_SIZE, self.num_tags).fill_(-10000.)
        score[:, SOS_IDX] = 0.

        for t in range(h.size(1)):  # recursion through the sequence
            mask_t = mask[:, t].unsqueeze(1)
            score_t = score.unsqueeze(1) + self.trans  # [B, 1, C] -> [B, C, C]
            score_t, bptr_t = score_t.max(2)  # best previous scores and tags
            score_t += h[:, t]  # plus emission scores
            bptr = torch.cat((bptr, bptr_t.unsqueeze(1)), 1)
            score = score_t * mask_t + score * (1 - mask_t)
        score += self.trans[EOS_IDX]
        best_score, best_tag = torch.max(score, 1)

        # back-tracking
        bptr = bptr.tolist()
        best_path = [[i] for i in best_tag.tolist()]
        for b in range(BATCH_SIZE):
            x = best_tag[b] # best tag
            y = int(mask[b].sum().item())
            for bptr_t in reversed(bptr[b][:y]):
                x = bptr_t[x]
                best_path[b].append(x)
            best_path[b].pop()
            best_path[b].reverse()

        return best_path


def Tensor(*args):
    x = torch.Tensor(*args)
    return x.cuda() if CUDA else x


def LongTensor(*args):
    x = torch.LongTensor(*args)
    return x.cuda() if CUDA else x


def randn(*args):
    x = torch.randn(*args)
    return x.cuda() if CUDA else x


def zeros(*args):
    x = torch.zeros(*args)
    return x.cuda() if CUDA else x


def log_sum_exp(x):
    m = torch.max(x, -1)[0]
    return m + torch.log(torch.sum(torch.exp(x - m.unsqueeze(-1)), -1))
