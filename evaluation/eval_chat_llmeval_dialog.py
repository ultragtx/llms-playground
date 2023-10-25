import os
import argparse
import json
import logging
from utils.custom_logging import setup_logging
import datetime
from transformers.trainer_utils import set_seed
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.generation import GenerationConfig
import random
import torch
import numpy as np
from peft import PeftModel, PeftConfig

logger = None

def parse_args():
    parser = argparse.ArgumentParser(description="LLMs evaluation.")

    parser.add_argument(
        "-c",
        "--checkpoint-path",
        type=str,
        required=True,
        help="HF model name or checkpoint path",
    )
    parser.add_argument(
        "-f",
        "--eval-data-file-path",
        type=str,
        required=True,
        help="Path of eval data"
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        required=True,
        help="Path of output directory"
    )
    parser.add_argument(
        "-s",
        "--seed",
        type=int,
        default=42,
        help="Random seed"
    )
    args = parser.parse_args()

    return args

def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    # ^^ safe to call this function even if cuda is not available

def read_eval_data(file_path):
    data = None

    try:
        with open(file_path, 'r') as json_file:
            data = json.load(json_file)
    except Exception as e:
        logging.error(f"An error occurred while reading the JSON file: {str(e)}")

    return data

def load_model_and_tokenizer(checkpoint_path):
    config = PeftConfig.from_pretrained(checkpoint_path)
    model_name = config.base_model_name_or_path

    tokenizer = AutoTokenizer.from_pretrained(
        model_name, trust_remote_code=True
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map="auto",
        trust_remote_code=True,
        bf16=True,
        use_flash_attn=True,
    )
    model = PeftModel.from_pretrained(model, checkpoint_path)
    model.eval()
    model.generation_config = GenerationConfig.from_pretrained(
        model_name, trust_remote_code=True
    )
    model.generation_config.do_sample = False  # use greedy decoding
    return model, tokenizer


def gen_output_file_path(args):
    base_name = os.path.basename(os.path.normpath(args.checkpoint_path))
    current_datetime = datetime.datetime.now()
    date_time_str = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")
    new_file_name = f"{base_name}_{date_time_str}.json"
    new_file_path = os.path.join(args.output_dir, new_file_name)

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    return new_file_path

def save_output(json_data, path):
    with open(path, 'w', encoding='utf-8') as json_file:
        json.dump(json_data, json_file, ensure_ascii=False, indent=2)


def start_evaluation(model, tokenizer, eval_data, output_data):
    total_count = len(eval_data)
    previous_question = None
    for index, e in enumerate(eval_data):
        # print(f"Processing Element {index}/{total_count}:", end='\r')
        print(f"Processing Element {index}/{total_count}")

        question_obj = e['dialog'][0]
        assert(question_obj['role'] == 'user')
        question = question_obj['content']

        if (previous_question == question):
            continue

        previous_question = question

        response, _ = model.chat(
            tokenizer,
            question,
            history=None,
        )

        logger.debug(f'Q: {question}')
        logger.debug(f'A: {response}')

        result = e
        result['dialog'].append({
            'role': "llm",
            'content': response,
        })

        output_data.append(result)

        # if index > 5:
        #     break



def main():
    setup_logging(console_output=True, log_level_console=logging.DEBUG)
    global logger
    logger = logging.getLogger(__name__)

    args = parse_args()

    logger.debug(f'arguments: {args}')

    eval_data = read_eval_data(args.eval_data_file_path)

    if not eval_data:
        return
    
    output_file_path = gen_output_file_path(args)

    logger.debug(f'Output file path: {output_file_path}')
    
    model, tokenizer = load_model_and_tokenizer(args.checkpoint_path)

    if not model or not tokenizer:
        logger.error('Model or tokenizer not found.')
        return
    
    output_json_data = []

    try:
        start_evaluation(
            model=model,
            tokenizer=tokenizer,
            eval_data=eval_data,
            output_data=output_json_data,
        )
    except Exception as e:
        logger.error(f"An error occurred while evaluating: {str(e)}")
    finally:
        save_output(output_json_data, output_file_path)


if __name__ == "__main__":
    main()
