import os
import csv
import copy
import json
import logging

import torch
from torch.utils.data import TensorDataset

from utils import get_label

logger = logging.getLogger(__name__)


class InputExample(object):
    """
    A single training/test example for simple sequence classification.

    Args:
        guid: Unique id for the example.
        text_a: string. The untokenized text of the first sequence. For single
        sequence tasks, only this sequence must be specified.
        label: (Optional) string. The label of the example. This should be
        specified for train and dev examples, but not for test examples.
    """

    def __init__(self, guid, text_a, label):
        self.guid = guid
        self.text_a = text_a
        self.label = label

    def __repr__(self):
        return str(self.to_json_string())

    def to_dict(self):
        """Serializes this instance to a Python dictionary."""
        output = copy.deepcopy(self.__dict__)
        return output

    def to_json_string(self):
        """Serializes this instance to a JSON string."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"


class InputFeatures(object):
    """
    A single set of features of data.

    Args:
        input_ids: Indices of input sequence tokens in the vocabulary.
        attention_mask: Mask to avoid performing attention on padding token indices.
            Mask values selected in ``[0, 1]``:
            Usually  ``1`` for tokens that are NOT MASKED, ``0`` for MASKED (padded) tokens.
        token_type_ids: Segment token indices to indicate first and second portions of the inputs.
    """

    def __init__(self, input_ids, attention_mask, token_type_ids, label_id,
                 e1_mask, e2_mask,li,lines2):
        self.input_ids = input_ids
        self.attention_mask = attention_mask
        self.token_type_ids = token_type_ids
        self.label_id = label_id
        self.e1_mask = e1_mask
        self.e2_mask = e2_mask
        self.li = li
        self.lines2 = lines2

    def __repr__(self):
        return str(self.to_json_string())

    def to_dict(self):
        """Serializes this instance to a Python dictionary."""
        output = copy.deepcopy(self.__dict__)
        return output

    def to_json_string(self):
        """Serializes this instance to a JSON string."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"


class PPIProcessor(object):
    """Processor for the Semeval data set """

    def __init__(self, args):
        self.args = args
        self.relation_labels = get_label(args)

    @classmethod
    def _read_tsv(cls, input_file, quotechar=None):
        """Reads a tab separated value file."""
        with open(input_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t", quotechar=quotechar)
            lines = []
            for line in reader:
                lines.append(line)
            return lines

    def _create_examples(self, lines, set_type):
        """Creates examples for the training and dev sets."""
        examples = []
        for (i, line) in enumerate(lines):
            guid = "%s-%s" % (set_type, i)
            text_a = line[1]
            if self.args.do_lower_case:
                text_a = text_a.lower()
            label = self.relation_labels.index(line[0])
            if i % 1000 == 0:
                logger.info(line)
            examples.append(InputExample(guid=guid, text_a=text_a, label=label))
        return examples

    def get_examples(self, mode):
        """
        Args:
            mode: train, dev, test
        """
        file_to_read = None
        if mode == 'train':
            file_to_read = self.args.train_file
        elif mode == 'dev':
            file_to_read = self.args.dev_file
        elif mode == 'test':
            file_to_read = self.args.test_file

        logger.info("LOOKING AT {}".format(os.path.join(self.args.data_dir, file_to_read)))
        return self._create_examples(self._read_tsv(os.path.join(self.args.data_dir, file_to_read)), mode)


processors = {
    "ppi": PPIProcessor
}


def convert_examples_to_features(examples, max_seq_len, tokenizer,model,
                                 cls_token_segment_id=0,
                                 pad_token_segment_id=0,
                                 sequence_a_segment_id=0,
                                 mask_padding_with_zero=True
                                 ):
    # Setting based on the current model type
    cls_token = tokenizer.cls_token  # 'cls'
    sep_token = tokenizer.sep_token  # 'sep'
    pad_token_id = tokenizer.pad_token_id  # 0

    features = []
    if model == 'train':
        f = open('./data/train_ju.tsv', 'r', encoding='utf-8-sig')
        lines = f.readlines()
        i=0
    if model == 'dev':
        f = open('./data/dev_ju.tsv', 'r', encoding='utf-8-sig')
        lines = f.readlines()
        i=0
    if model == 'test':
        f = open('./data/test_ju.tsv', 'r', encoding='utf-8-sig')
        lines = f.readlines()
        i=0
    for (ex_index, example) in enumerate(examples):
        a,b=lines[i].strip().split('\t')
        a_li=[]
        a_buchong=[]
        li=int(a)

        b=b.replace("'",'')
        b=b.replace('[','')
        b=b.replace(']','')

        c=b.split(',')

        for i in range(len(c)):
            i=int(c[i])
            a_li.append(i)
        a_buchong=[0]*(400-len(a_li))
        lines2=a_li+a_buchong
        #b=int(b)
        #aaa=aaa.split('\0')
        i=i+1
        if ex_index % 5000 == 0:
            logger.info("Writing example %d of %d" % (ex_index, len(examples)))

        tokens_a = tokenizer.tokenize(example.text_a)
        logger.info("Writing example %d of %d" % (ex_index, len(examples)))

        e11_p = tokens_a.index("<e1>")  # the start position of entity1
        e12_p = tokens_a.index("</e1>")  # the end position of entity1
        e21_p = tokens_a.index("<e2>")  # the start position of entity2
        e22_p = tokens_a.index("</e2>")  # the end position of entity2
        # e11_p = tokens_a.index("PROTEIN1")  # the start position of entity1
        # e12_p = e11_p + 1  # the end position of entity1
        # e11_p = e11_p - 1
        # e21_p = tokens_a.index("PROTEIN2")  # the start position of entity2
        # e22_p = e22_p + 1  # the end position of entity2
        # e21_p = e21_p - 1

        # Replace the token
        tokens_a[e11_p] = "$"
        tokens_a[e12_p] = "$"
        tokens_a[e21_p] = "#"
        tokens_a[e22_p] = "#"

        # Add 1 because of the [CLS] token
        e11_p += 1
        e12_p += 1
        e21_p += 1
        e22_p += 1

        # Account for [CLS] and [SEP] with "- 2" and with "- 3" for RoBERTa.
        special_tokens_count = 2
        if len(tokens_a) > max_seq_len - special_tokens_count:
            tokens_a = tokens_a[:(max_seq_len - special_tokens_count)]

        tokens = tokens_a
        tokens += [sep_token]

        token_type_ids = [sequence_a_segment_id] * len(tokens)

        tokens = [cls_token] + tokens
        token_type_ids = [cls_token_segment_id] + token_type_ids

        input_ids = tokenizer.convert_tokens_to_ids(tokens)

        # The mask has 1 for real tokens and 0 for padding tokens. Only real
        # tokens are attended to.
        attention_mask = [1 if mask_padding_with_zero else 0] * len(input_ids)

        # Zero-pad up to the sequence length.
        padding_length = max_seq_len - len(input_ids)
        input_ids = input_ids + ([pad_token_id] * padding_length)
        attention_mask = attention_mask + ([0 if mask_padding_with_zero else 1] * padding_length)
        token_type_ids = token_type_ids + ([pad_token_segment_id] * padding_length)

        # e1 mask, e2 mask
        e1_mask = [0] * len(attention_mask)
        e2_mask = [0] * len(attention_mask)

        for i in range(e11_p, e12_p + 1):
            e1_mask[i] = 1
        for i in range(e21_p, e22_p + 1):
            e2_mask[i] = 1

        assert len(input_ids) == max_seq_len, "Error with input length {} vs {}".format(len(input_ids), max_seq_len)
        assert len(attention_mask) == max_seq_len, "Error with attention mask length {} vs {}".format(len(attention_mask), max_seq_len)
        assert len(token_type_ids) == max_seq_len, "Error with token type length {} vs {}".format(len(token_type_ids), max_seq_len)

        label_id = int(example.label)
        if ex_index < 5:
            logger.info("*** Example ***")
            logger.info("guid: %s" % example.guid)
            logger.info("tokens: %s" % " ".join([str(x) for x in tokens]))
            logger.info("input_ids: %s" % " ".join([str(x) for x in input_ids]))
            logger.info("attention_mask: %s" % " ".join([str(x) for x in attention_mask]))
            logger.info("token_type_ids: %s" % " ".join([str(x) for x in token_type_ids]))
            logger.info("label: %s (id = %d)" % (example.label, label_id))
            logger.info("e1_mask: %s" % " ".join([str(x) for x in e1_mask]))
            logger.info("e2_mask: %s" % " ".join([str(x) for x in e2_mask]))

        features.append(
            InputFeatures(input_ids=input_ids,
                          attention_mask=attention_mask,
                          token_type_ids=token_type_ids,
                          label_id=label_id,
                          e1_mask=e1_mask,
                          e2_mask=e2_mask,
                          li=li,
                          lines2=lines2,))
    f.close()

    return features


def load_and_cache_examples(args, tokenizer, mode):
    processor = processors[args.task](args)  # 处理器

    # Load data features from cache or dataset file
    cached_file_name = 'cached_{}_{}_{}_{}'.format(
        args.task, list(filter(None, args.pretrained_model_name.split("/"))).pop(), args.max_seq_len, mode)
    if args.do_lower_case:
        cached_file_name = cached_file_name + '_lower'

    cached_features_file = os.path.join(args.data_dir, cached_file_name)
    # 如果缓存文件存在
    if os.path.exists(cached_features_file):
        logger.info("Loading features from cached file %s", cached_features_file)
        # 加载特征（内部函数）attention_mask,e1_mask,e2_mask,input_ids,label_id,token_type_ids
        features = torch.load(cached_features_file)
    else:
        # 不存在则下载
        logger.info("Creating features from dataset file at %s", args.data_dir)
        # 如果mode为训练集，把训练集实例加载进来
        if mode == "train":
            examples = processor.get_examples("train")
        elif mode == "dev":
            examples = processor.get_examples("dev")
        elif mode == "test":
            examples = processor.get_examples("test")
        else:
            raise Exception("For mode, Only train, dev, test is available")

        features = convert_examples_to_features(examples, args.max_seq_len, tokenizer,mode)
        logger.info("Saving features into cached file %s", cached_features_file)
        torch.save(features, cached_features_file)

    # Convert to Tensors and build dataset(转成tensor 构建数据集)
    all_input_ids = torch.tensor([f.input_ids for f in features], dtype=torch.long)
    all_attention_mask = torch.tensor([f.attention_mask for f in features], dtype=torch.long)
    all_token_type_ids = torch.tensor([f.token_type_ids for f in features], dtype=torch.long)
    all_e1_mask = torch.tensor([f.e1_mask for f in features], dtype=torch.long)  # add e1 mask
    all_e2_mask = torch.tensor([f.e2_mask for f in features], dtype=torch.long)  # add e2 mask

    all_label_ids = torch.tensor([f.label_id for f in features], dtype=torch.long)

    all_lines = torch.tensor([f.li for f in features], dtype=torch.long)  # add e2 mask
    all_lines2 = torch.tensor([f.lines2 for f in features], dtype=torch.long)  # add e2 mask


    dataset = TensorDataset(all_input_ids, all_attention_mask,
                            all_token_type_ids, all_label_ids, all_e1_mask, all_e2_mask,all_lines,all_lines2)
    return dataset
