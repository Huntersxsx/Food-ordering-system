UNIT = "word"  # unit of tokenization (char, word)

MIN_LEN = 1  # minimum sequence length for training
MAX_LEN = 150  # maximum sequence length for decoding
KEEP_IDX = False  # use the existing indices

BATCH_SIZE = 256
EMBED_SIZE = 300
HIDDEN_SIZE = 1000
NUM_LAYERS = 2
DROPOUT = 0.5
BIDIRECTIONAL = True
NUM_DIRS = 2 if BIDIRECTIONAL else 1
LEARNING_RATE = 1e-4
SAVE_EVERY = 1

PAD = "<PAD>"  # padding
SOS = "<SOS>"  # start of sequence
EOS = "<EOS>"  # end of sequence
UNK = "<UNK>"  # unknown token

PAD_IDX = 0
SOS_IDX = 1
EOS_IDX = 2
UNK_IDX = 3

#   CUDA_VISIBLE_DEVICES=1 python prepare.py seg_train_data.txt
#   CUDA_VISIBLE_DEVICES=1 python train.py model.epoch0 seg_train_data.word_to_idx seg_train_data.tag_to_idx seg_train_data.csv 50
#   CUDA_VISIBLE_DEVICES=1 python predict.py model.epoch10 seg_train_data.word_to_idx seg_train_data.tag_to_idx seg_test_data.txt
#   CUDA_VISIBLE_DEVICES=1 python evaluate.py model.epoch10 seg_train_data.word_to_idx seg_train_data.tag_to_idx seg_test_data.txt
