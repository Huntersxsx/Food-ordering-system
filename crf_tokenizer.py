from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import glob
import logging
import os
import shutil
import torch
import torch.nn as nn
from model import *
import re

from rasa_nlu.components import Component
from rasa_nlu.config import RasaNLUModelConfig
from rasa_nlu.tokenizers import Tokenizer, Token
from rasa_nlu.training_data import Message, TrainingData
from typing import Any, List, Text

logger = logging.getLogger(__name__)

CRF_CUSTOM_DICTIONARY_PATH = "tokenizer_crf"


class CRFTokenizer(Tokenizer, Component):
    name = "tokenizer_crf"

    provides = ["tokens"]

    language_list = ["zh"]

    defaults = {
        "crf_model": "./crf_tokenizer/checkpoints",
        "word2i": "./crf_tokenizer/dict/seg_train_data.word_to_idx", 
        "tag2i": "./crf_tokenizer/dict/seg_train_data.tag_to_idx", 
        "dictionary_path": "./custom_tokenizer/user_dict",  # default don't load custom dictionary
        "split_path": "./custom_tokenizer/split_dict"
    }

    def __init__(self, component_config=None):
        # type: (Dict[Text, Any]) -> None

        super(CRFTokenizer, self).__init__(component_config)
        # path to dictionary file or None
        self.dictionary_path = self.component_config.get('dictionary_path')
        self.split_path = self.component_config.get('split_path')
        self.word2i = self.load_word_to_idx(self.component_config.get("word2i"))
        self.tag2i = self.load_tag_to_idx(self.component_config.get("tag2i"))

        file_name = self.component_config.get("name")
        self.checkpoint = os.path.join(self.component_config.get("crf_model"), file_name)


    @staticmethod
    def load_word_to_idx(filename):
        word_to_idx = {}
        fo = open(filename, 'r', encoding='UTF-8')
        for line in fo:
            line = line.strip()
            word_to_idx[line] = len(word_to_idx)
        fo.close()
        return word_to_idx

    @staticmethod
    def load_tag_to_idx(filename):
        tag_to_idx = {}
        fo = open(filename, 'r', encoding='UTF-8')
        for line in fo:
            line = line.strip()
            tag_to_idx[line] = len(tag_to_idx)
        fo.close()
        return tag_to_idx

    @staticmethod
    def load_checkpoint(filename, model=None):
        if CUDA:
            checkpoint = torch.load(filename)
        else:
            checkpoint = torch.load(filename, map_location='cpu')
        if model:
            model.load_state_dict(checkpoint["state_dict"])
        epoch = checkpoint["epoch"]
        loss = checkpoint["loss"]
        return epoch


    def LongTensor(*args):
        x = torch.LongTensor(*args)
        return x.cuda() if CUDA else x

    def Mycut(self,text):
        word_to_idx = self.word2i
        tag_to_idx = self.tag2i
        idx_to_tag = [tag for tag, _ in sorted(tag_to_idx.items(), key=lambda x: x[1])]
        model = lstm_crf(len(word_to_idx), len(tag_to_idx))
        model.eval()  # 将模型变成测试模式
        self.load_checkpoint(self.checkpoint, model)

        idx = 0
        data = []
        w = [i for i in text]
        x = [word_to_idx[i] if i in word_to_idx else UNK_IDX for i in w]
        data.append([idx, w, x])

        while len(data) < BATCH_SIZE:
            data.append([-1, "", [EOS_IDX]])    # 补到BATCH_SIZE个句子

        data.sort(key=lambda x: -len(x[2]))   #  根据句子长短进行排序
        batch_len = len(data[0][2])
        batch = [x[2] + [PAD_IDX] * (batch_len - len(x[2])) for x in data]  # padding
        result = model.decode(LongTensor(batch))  # 解码 [[],[]……[]]


        ix = 0
        for j in range(len(result[0])):
            if idx_to_tag[result[0][j]] == 'e' or idx_to_tag[result[0][j]] == 's':   # 如果标签是e或s
                data[0][1].insert(j + 1 + ix, '<>')     
                ix += 1

        data[0][1].pop()
        aftercut = ''.join(data[0][1])

        return aftercut

    def add_userdict(self, aftercut):
        if self.dictionary_path is not None:
            user_dicts = glob.glob("{}/*".format(self.dictionary_path))
            for ud in user_dicts:
                f = open(ud, "r", encoding='UTF-8')
                new_word = []   #  新增词
                for line in f:
                    line = line.strip()
                    new_word.append(line)
                f.close()
                s = '<>' + aftercut + '<>'
                for w in new_word:
                    pattern = '(<>)?'
                    for ch in w:
                        pattern = pattern + ch + '(<>)?'
                    #pattern = pattern[:-1]     #  （<>)?巨(<>)?无(<>)?霸(<>)?  
                    s = re.sub(pattern, '<>' + w + '<>', s)   #  替换成   <>巨无霸<>
                aftercut = s[2:-2]   #  去掉首尾<>
        return aftercut


    def split_userdict(self, aftercut):
        if self.split_path is not None:
            user_dicts = glob.glob("{}/*".format(self.split_path))
            for ud in user_dicts:
                f = open(ud, "r", encoding='UTF-8')
                new_word = []   #  新增词
                for line in f:
                    line = line.strip()
                    new_word.append(line)
                f.close()
                s = aftercut
                for w in new_word:
                    pattern = '(<>)?' + w + '(<>)?'
                    s = re.sub(pattern, '<>' + w + '<>', s)
                s = re.sub('<><>', '<>', s)
                aftercut = s
        return aftercut


    def train(self, training_data, config, **kwargs):
        # type: (TrainingData, RasaNLUModelConfig, **Any) -> None
        for example in training_data.training_examples:
            example.set("tokens", self.tokenize(example.text))

    def process(self, message, **kwargs):
        # type: (Message, **Any) -> None
        message.set("tokens", self.tokenize(message.text))

    def tokenize(self, text):
        # type: (Text) -> List[Token]
        seg = self.Mycut(text)
        seg = self.add_userdict(seg)
        seg = self.split_userdict(seg)
        seg = seg.split('<>')

        tokens = []
        i = 0
        for w in seg:
            tokens.append(Token(w, i))
            i += len(w)
        return tokens

    def persist(self, model_dir):
        # type: (Text) -> Optional[Dict[Text, Any]]
        """Persist this model into the passed directory."""

        model_dictionary_path = None

        # copy custom dictionaries to model dir, if any
        if self.dictionary_path is not None:
            target_dictionary_path = os.path.join(model_dir,CRF_CUSTOM_DICTIONARY_PATH)

            self.copy_files_dir_to_dir(self.dictionary_path,
                                       target_dictionary_path)

            # set dictionary_path of model metadata to relative path
            model_dictionary_path = CRF_CUSTOM_DICTIONARY_PATH

        return {"classifier_file": self.name, "dictionary_path": model_dictionary_path}


    @classmethod
    def load(cls,
             model_dir=None,  # type: Optional[Text]
             model_metadata=None,  # type: Optional[Metadata]
             cached_component=None,  # type: Optional[Component]
             **kwargs  # type: **Any
             ):
        # type: (...) -> JiebaTokenizer

        meta = model_metadata.for_component(cls.name)
        relative_dictionary_path = meta.get("dictionary_path")

        # get real path of dictionary path, if any
        if relative_dictionary_path is not None:
            dictionary_path = os.path.join(model_dir, relative_dictionary_path)

            meta["dictionary_path"] = dictionary_path

        return cls(meta)

    @staticmethod
    def copy_files_dir_to_dir(input_dir, output_dir):
        # make sure target path exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        target_file_list = glob.glob("{}/*".format(input_dir))
        for target_file in target_file_list:
            shutil.copy2(target_file, output_dir)
